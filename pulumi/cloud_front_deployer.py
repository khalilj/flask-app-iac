import pulumi_aws as aws
import pulumi

class CloudFrontDeployer:
    def __init__(self, cf_name, s3_bucket, env):
        self.cf_name = cf_name
        self.env = env
        self.s3_bucket = s3_bucket
    
    def create(self):
        site_bucket = aws.s3.Bucket(self.s3_bucket, bucket=self.s3_bucket,
            acl="public-read",
            tags={
                "Environment": self.env,
                "Name": self.s3_bucket,
            })

        s3_origin_id = "salt-site-s3"
        s3_distribution = aws.cloudfront.Distribution(self.cf_name,
            origins=[aws.cloudfront.DistributionOriginArgs(
                domain_name=site_bucket.bucket_regional_domain_name,
                origin_id=s3_origin_id
            )],
            enabled=True,
            comment="Salt portal",
            default_root_object="index.html",
            tags={
                "Environment": self.env,
            },
            default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
                allowed_methods=[
                    "DELETE",
                    "GET",
                    "HEAD",
                    "OPTIONS",
                    "PATCH",
                    "POST",
                    "PUT",
                ],
                cached_methods=[
                    "GET",
                    "HEAD",
                ],
                target_origin_id=s3_origin_id,
                forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                    query_string=False,
                    cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                        forward="none",
                    ),
                ),
                viewer_protocol_policy="allow-all",
                min_ttl=0,
                default_ttl=3600,
                max_ttl=86400,
            ),
            restrictions=aws.cloudfront.DistributionRestrictionsArgs(
                geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                    restriction_type="none",
                    locations=[
                    ],
                ),
            ),
            viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
                cloudfront_default_certificate=True,
            )
        )

        pulumi.export('s3_distribution.domain_name', s3_distribution.domain_name)