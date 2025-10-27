import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const stack = pulumi.getStack();

if (stack === "common") {
  const bucketName = config.require("serverlessBucketName");

  const bucket = new aws.s3.Bucket("serverlessBucket", {
    bucket: bucketName,
    forceDestroy: false,
  });

  new aws.s3.BucketVersioning(bucketName, {
    bucket: bucket.id,
    versioningConfiguration: {
      status: "Suspended",
    },
  });

  new aws.s3.BucketServerSideEncryptionConfiguration(bucketName, {
    bucket: bucket.id,
    rules: [
      {
        applyServerSideEncryptionByDefault: {
          sseAlgorithm: "AES256",
        },
      },
    ],
  });

  new aws.s3.BucketPublicAccessBlock(bucketName, {
    bucket: bucket.id,
    blockPublicAcls: true,
    blockPublicPolicy: true,
    ignorePublicAcls: true,
    restrictPublicBuckets: true,
  });

  new aws.s3.BucketOwnershipControls(bucketName, {
    bucket: bucket.id,
    rule: {
      objectOwnership: "BucketOwnerPreferred",
    },
  });
}
