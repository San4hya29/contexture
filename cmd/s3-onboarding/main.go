// Package main provides an S3 onboarding tool that verifies end-to-end
// connectivity with a MinIO/S3-compatible storage backend. It tests bucket
// creation, file upload, and file download operations.
package main

import (
	"context"
	"log"
	"os"
	"path/filepath"

	storage "github.com/sodafoundation/contexture/pkg/ocs/storage"
)

func main() {
	// Load S3 configuration from YAML
	cfg, err := storage.LoadS3Config("config/s3_config.yaml")
	if err != nil {
		log.Fatalf("Failed to load S3 config: %v", err)
	}

	// Initialize the S3 client
	client, err := storage.NewS3Client(cfg)
	if err != nil {
		log.Fatalf("Failed to create S3 client: %v", err)
	}

	ctx := context.Background()
	bucketName := cfg.BucketName

	// Step 1: Create bucket
	log.Printf("Creating bucket: %s", bucketName)
	if err := client.CreateBucket(ctx, bucketName); err != nil {
		log.Fatalf("Failed to create bucket: %v", err)
	}
	log.Printf("Bucket '%s' created successfully", bucketName)

	// Step 2: Upload a test file
	testFile := "config/s3_config.yaml"
	objectName := filepath.Base(testFile)
	log.Printf("Uploading file: %s -> %s/%s", testFile, bucketName, objectName)
	if err := client.UploadFile(ctx, bucketName, objectName, testFile); err != nil {
		log.Fatalf("Failed to upload file: %v", err)
	}
	log.Printf("File uploaded successfully")

	// Step 3: Download the file
	downloadPath := "/tmp/downloaded_" + objectName
	log.Printf("Downloading file: %s/%s -> %s", bucketName, objectName, downloadPath)
	if err := client.DownloadFile(ctx, bucketName, objectName, downloadPath); err != nil {
		log.Fatalf("Failed to download file: %v", err)
	}
	log.Printf("File downloaded successfully to %s", downloadPath)

	// Verify download
	info, err := os.Stat(downloadPath)
	if err != nil {
		log.Fatalf("Downloaded file not found: %v", err)
	}
	log.Printf("S3 onboarding complete — verified file size: %d bytes", info.Size())
}
