CLOUDFRONT_DISTRIBUTION_ID=E55YMKDCUQ9V8

aws s3 sync --delete ./site s3://persianpapa.com
aws cloudfront create-invalidation --paths /* --distribution-id $CLOUDFRONT_DISTRIBUTION_ID
