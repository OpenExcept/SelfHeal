import { AwsCrc32c } from "@aws-crypto/crc32c";
import { ChecksumAlgorithm } from "./constants";
import { getCrc32ChecksumAlgorithmFunction } from "./getCrc32ChecksumAlgorithmFunction";
export const selectChecksumAlgorithmFunction = (checksumAlgorithm, config) => ({
    [ChecksumAlgorithm.MD5]: config.md5,
    [ChecksumAlgorithm.CRC32]: getCrc32ChecksumAlgorithmFunction(),
    [ChecksumAlgorithm.CRC32C]: AwsCrc32c,
    [ChecksumAlgorithm.SHA1]: config.sha1,
    [ChecksumAlgorithm.SHA256]: config.sha256,
}[checksumAlgorithm]);
