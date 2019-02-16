# Remarks:
- Updating CloudFront is SLOW. Don't panic.

# Quirks:
We're creating an S3 bucket that's enabled as a website. This is beneficial because it will handle
redirects such as mysite.com/asd -> mysite.com/asd/index.html.

# TODOS:
- "If you use an Amazon S3 bucket configured as a website endpoint, you must set it up with CloudFront as a custom origin and you can't use the origin access identity feature described in this topic. You can restrict access to content on a custom origin by using custom headers. For more information, see Using Custom Headers to Restrict Access to Your Content on a Custom Origin."(https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html#private-content-granting-permissions-to-oai)(https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/forward-custom-headers.html#forward-custom-headers-restrict-access)
- TLS + optional http-allow (be able to spin up stack, _then_ request cert and apply it)
- Create build script that moves site/ to dist/, does gzip, etc.
- Support www.persianpapa.com