import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { createReadStream, createWriteStream } from 'fs';
import { dirname } from 'path';
import { mkdir } from 'fs/promises';
import { Readable } from 'stream';

export class S3Storage {
  private s3Client: S3Client;

  constructor() {
    this.s3Client = new S3Client({});
  }

  async putObject(bucketName: string, filePath: string, s3Key: string): Promise<boolean> {
    try {
      const fileStream = createReadStream(filePath);
      
      await this.s3Client.send(new PutObjectCommand({
        Bucket: bucketName,
        Key: s3Key,
        Body: fileStream
      }));

      console.log(`Successfully uploaded ${filePath} to s3://${bucketName}/${s3Key}`);
      return true;
    } catch (error) {
      console.error('Failed to upload file to S3:', error);
      return false;
    }
  }

  async getObject(bucketName: string, s3Key: string, localPath: string): Promise<boolean> {
    try {
      const response = await this.s3Client.send(new GetObjectCommand({
        Bucket: bucketName,
        Key: s3Key
      }));

      if (!response.Body) {
        throw new Error('Response body is undefined');
      }

      if (!(response.Body instanceof Readable)) {
        throw new Error('Response body is not a readable stream');
      }

      await mkdir(dirname(localPath), { recursive: true });
      const fileStream = createWriteStream(localPath);
      
      await new Promise<void>((resolve, reject) => {
        (response.Body as Readable).pipe(fileStream)
          .on('error', reject)
          .on('finish', resolve);
      });

      console.log(`Successfully downloaded s3://${bucketName}/${s3Key} to ${localPath}`);
      return true;
    } catch (error) {
      console.error('Failed to download file from S3:', error);
      return false;
    }
  }

  async deleteObject(bucketName: string, s3Key: string): Promise<boolean> {
    try {
      await this.s3Client.send(new DeleteObjectCommand({
        Bucket: bucketName,
        Key: s3Key
      }));
      
      console.log(`Successfully deleted s3://${bucketName}/${s3Key}`);
      return true;
    } catch (error) {
      console.error('Failed to delete file from S3:', error);
      return false;
    }
  }

  async listObjects(bucketName: string, prefix?: string): Promise<string[]> {
    try {
      const command = new ListObjectsV2Command({
        Bucket: bucketName,
        Prefix: prefix
      });
      
      const response = await this.s3Client.send(command);
      return (response.Contents || []).map(obj => obj.Key || '');
    } catch (error) {
      console.error('Failed to list objects in S3:', error);
      return [];
    }
  }
} 