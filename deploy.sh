CLOUDFRONT_DISTRIBUTION_ID=E55YMKDCUQ9V8
BUCKET=persianpapa.com
REDIRECT_BASE=https://persianpapa.com
REDIRECT_DEFINITION=./redirects.yml

aws s3 sync --delete ./site s3://$BUCKET
python3 add_website_redirects.py --bucket $BUCKET --destination-base $REDIRECT_BASE --definition-file $REDIRECT_DEFINITION
aws cloudfront create-invalidation --paths '/*' --distribution-id $CLOUDFRONT_DISTRIBUTION_ID
