import json
import os
import inspect
import functools
import datetime
import traceback
import sys
import logging
from typing import Any, Callable, Dict, Optional, Type, Tuple, List
from pathlib import Path
import litellm
from selfheal.slack import SlackAlertBot

# Configure standard logger
logger = logging.getLogger("healing")
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class FunctionDebugger:
    def __init__(self, dump_dir: str = "/root/debug_states", use_s3: bool = False, slack_token: Optional[str] = None):
        """
        Initialize the FunctionDebugger.
        
        Args:
            dump_dir (str): Directory to store debug dumps
            use_s3 (bool): Whether to also store dumps in S3 (default: False)
            slack_token (str): Slack Bot User OAuth Token for alerts
        """
        self.dump_dir = Path(dump_dir)
        self.dump_dir.mkdir(exist_ok=True, parents=True)
        self.use_s3 = use_s3
        
        # Initialize Slack bot if token provided
        self.slack_bot = None
        if slack_token:
            self.slack_bot = SlackAlertBot(slack_token)
        
        # Only initialize S3 if needed
        if self.use_s3:
            try:
                from selfheal.s3_storage import S3Storage
                self.s3_storage = S3Storage()
                self.s3_bucket = "debug-state-dumps"
                logger.info("S3 storage initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 storage: {e}. Falling back to local storage only.")
                self.use_s3 = False

    def _get_constructor_args(self, instance: Any) -> Tuple[Dict[str, str], str]:
        """Extract constructor arguments from an instance using __init__ signature."""
        try:
            # Check if instance is a primitive type
            if isinstance(instance, (str, int, float, bool, bytes)):
                return {}, f"No constructor args - primitive type: {type(instance).__name__}"

            init_signature = inspect.signature(instance.__class__.__init__)

            # Get all instance attributes
            instance_attrs = {k: str(v) for k, v in getattr(instance, '__dict__', {}).items()
                            if not k.startswith('_') and not callable(v)}

            # Match signature parameters with instance attributes
            constructor_args = {}
            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue
                if param_name in instance_attrs:
                    constructor_args[param_name] = instance_attrs[param_name]

            try:
                constructor_code = inspect.getsource(instance.__class__.__init__)
            except (TypeError, OSError):
                constructor_code = "Source code not available for built-in/dynamic class"

            return constructor_args, constructor_code

        except Exception as e:
            logger.warning(f"Could not fully capture constructor arguments: {e}")
            return {}, ""

    def _generate_dump_path(self, function_name: str) -> Path:
        """Generate a unique path for the debug dump file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{function_name}_{timestamp}.json"
        dump_path = self.dump_dir / filename
        return dump_path

    def _generate_s3_key(self, function_name: str) -> str:
        """Generate file key for the debug dump file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{function_name}_{timestamp}.json"

    def _dump_state(self, dump_path: Path, debug_state: Dict) -> Optional[str]:
        """
        Save the debug state to a JSON file and optionally to S3.
        Returns the file path or S3 URI if successful, None otherwise.
        """
        try:
            # Convert all values to strings to ensure JSON serialization
            debug_state = {k: str(v) if not isinstance(v, (dict, list, str, int, float, bool, type(None)))
                          else v for k, v in debug_state.items()}

            # Save locally
            with open(dump_path, 'w') as f:
                json.dump(debug_state, f, indent=2)

            logger.info(f"Saved debug dump to: {dump_path}")
            
            # If S3 is enabled, also save to S3
            if self.use_s3:
                try:
                    s3_key = self._generate_s3_key(dump_path.stem)
                    self.s3_storage.put_object(
                        bucket_name=self.s3_bucket,
                        file_path=str(dump_path),
                        s3_key=s3_key
                    )
                    s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
                    logger.info(f"Uploaded debug dump to S3: {s3_uri}")
                    return s3_uri
                except Exception as e:
                    logger.error(f"Failed to upload to S3: {e}. Using local path instead.")
            
            return str(dump_path)
        except Exception as e:
            logger.error(f"Failed to save debug dump: {e}")
            return None

    def _get_frame_info(self, frame) -> Dict:
        """Extract relevant information from a frame."""
        try:
            return {
                'filename': frame.f_code.co_filename,
                'function_name': frame.f_code.co_name,
                'line_number': frame.f_lineno,
                'local_vars': {k: str(v) for k, v in frame.f_locals.items()},
                'function_code': inspect.getsource(frame.f_code) if frame.f_code.co_filename != '<string>' else 'N/A'
            }
        except Exception as e:
            logger.warning(f"Failed to extract frame info: {e}")
            return {
                'filename': getattr(frame.f_code, 'co_filename', 'unknown'),
                'function_name': getattr(frame.f_code, 'co_name', 'unknown'),
                'line_number': getattr(frame, 'f_lineno', -1),
                'local_vars': {},
                'function_code': 'Failed to extract code'
            }

    def _get_stack_frames(self, tb, max_frames: int = 5) -> List[Dict]:
        """
        Get information from frames in the call stack, starting from where the exception occurred
        and walking backwards through the calling functions.
        """
        frames = []

        # First get to the frame where the exception occurred
        current = tb
        while current.tb_next:
            current = current.tb_next

        # Start with the current frame
        current_frame = current.tb_frame

        # Walk backwards through the call stack
        while current_frame and len(frames) < max_frames:
            try:
                # Skip frames from healing.py
                if 'healing.py' not in current_frame.f_code.co_filename:
                    frame_info = self._get_frame_info(current_frame)
                    frames.append(frame_info)
                current_frame = current_frame.f_back
            except Exception as e:
                logger.warning(f"Failed to get frame info: {e}")
                break

        return frames # Return frames in order from most recent to oldest

    def analyze(self, debug_state_path: str) -> str:
        """
        Analyze debug state using GPT-4 to identify potential issues and suggest fixes.
        """
        try:
            # Load the debug state from JSON file
            with open(debug_state_path, 'r') as f:
                debug_state = json.load(f)

            # Prepare a clean version of stack frames with abbreviated large variables
            clean_frames = []
            for frame in debug_state.get('stack_frames', []):
                clean_frame = {
                    'filename': frame['filename'],
                    'function_name': frame['function_name'],
                    'line_number': frame['line_number'],
                    'function_code': frame['function_code'],
                    'local_vars': {
                        k: str(v)[:500] + '...(truncated)' if len(str(v)) > 500 else v
                        for k, v in frame.get('local_vars', {}).items()
                    }
                }
                clean_frames.append(clean_frame)

            system_text = """You are a Python debugging expert. Your task is to analyze error information and stack traces to:
1. Identify the root cause of the error
2. Explain the execution flow that led to the error
3. Suggest specific fixes and improvements

Focus on the actual error and code logic rather than infrastructure or environment issues.
Provide clear, actionable insights that will help developers fix the issue."""

            user_text = f"""I need help analyzing this Python error. Here's the debug information:

Exception Details:
- Type: {debug_state['exception']['type']}
- Message: {debug_state['exception']['message']}

Traceback:
{debug_state['exception']['traceback']}

Stack Frames (ordered from most recent to oldest):
{json.dumps(clean_frames, indent=2)}

Please provide in simple and actionable terms:
1. What exactly caused this error?
2. How should we fix this issue?"""

            logger.info("Sending request to LLM to analyze debug state")
            messages = [
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text}
            ]
            
            response = litellm.completion(
                model="openai/gpt-4o", 
                messages=messages,
                temperature=0
            )
            
            # Extract the response content
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Failed to analyze debug state: {str(e)}")
            return f"Error analyzing debug state: {str(e)}"

    def _send_slack_alert(self, func_name: str, exception: Exception, debug_state_path: str) -> Optional[str]:
        """Send a Slack alert about the exception and debug state."""
        if not self.slack_bot:
            return None
            
        try:
            # Create the main alert message
            alert_message = (
                f"🚨 Exception in function `{func_name}`\n"
                f"*Type:* `{type(exception).__name__}`\n"
                f"*Message:* {str(exception)}"
            )
            
            # Send the main alert
            response = self.slack_bot.send_alert(alert_message, severity="error")
            thread_ts = response['ts']
            
            # Create clickable link to debug state viewer
            viewer_url = f"http://openexcept.com?debug_path={debug_state_path}"
            self.slack_bot.reply_to_thread(
                thread_ts=thread_ts,
                message=f"View debug state: <{viewer_url}|Open in Viewer>",
                severity="info"
            )
            
            return thread_ts
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return None

    def debug_enabled(self, dump_on_exception: bool = True):
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if dump_on_exception:
                        # Get stack frames information first
                        stack_frames = self._get_stack_frames(e.__traceback__)

                        if not stack_frames:
                            logger.warning("No stack frames captured")
                            raise

                        # Get information about the class if this is a method
                        is_class_method = False
                        class_info = None
                        instance_state = None

                        # Get the actual frame where the exception occurred
                        current = e.__traceback__
                        while current.tb_next:
                            current = current.tb_next
                        frame = current.tb_frame

                        if 'self' in frame.f_locals:
                            instance = frame.f_locals['self']
                            is_class_method = True
                            constructor_args, constructor_code = self._get_constructor_args(instance)

                            try:
                                class_code = inspect.getsource(instance.__class__)
                            except (TypeError, OSError):
                                class_code = "Source code not available for built-in/dynamic class"

                            class_info = {
                                'class_name': instance.__class__.__name__,
                                'module_name': instance.__class__.__module__,
                                'constructor_args': constructor_args,
                                'constructor_code': constructor_code,
                                'class_code': class_code
                            }

                            if isinstance(instance, (str, int, float, bool, bytes)):
                                instance_state = {
                                    'value': str(instance),
                                    'type': type(instance).__name__
                                }
                            else:
                                instance_state = {
                                    k: str(v) for k, v in getattr(instance, '__dict__', {}).items()
                                    if not k.startswith('_') and not callable(v)
                                }

                        debug_state = {
                            'exception': {
                                'type': type(e).__name__,
                                'message': str(e),
                                'traceback': traceback.format_exc()
                            },
                            'is_class_method': is_class_method,
                            'class_info': class_info,
                            'instance_state': instance_state,
                            'stack_frames': stack_frames
                        }

                        dump_path = self._generate_dump_path(func.__name__)
                        file_path = self._dump_state(dump_path, debug_state)
                        debug_state['file_path'] = file_path

                        # Send Slack alert with debug state
                        thread_ts = self._send_slack_alert(
                            func_name=func.__name__,
                            exception=e,
                            debug_state_path=file_path
                        )
                        
                        # Store the debug info in the exception object
                        setattr(e, 'debug_dump_path', file_path)
                        if thread_ts:
                            setattr(e, 'slack_thread_ts', thread_ts)

                    raise
            return wrapper
        return decorator

    def debug_class(self, dump_on_exception: bool = True):
        """Class decorator that enables debugging for all methods in a class."""
        def decorator(cls):
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                if not name.startswith('_') and not isinstance(method, property):
                    setattr(cls, name, self.debug_enabled(dump_on_exception)(method))
            return cls
        return decorator

    def debug_module(self, module):
        """Apply debug_enabled to all functions and class methods in a module."""
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                setattr(module, name, self.debug_enabled()(obj))
            elif inspect.isclass(obj):
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith('_'):
                        setattr(obj, method_name, self.debug_enabled()(method))
        return module