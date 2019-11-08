include Makefile.mk

NAME=cfn-ses-provider
S3_BUCKET_PREFIX=binxio-public
AWS_REGION=eu-central-1
ALL_REGIONS=$(shell printf "import boto3\nprint '\\\n'.join(map(lambda r: r['RegionName'], boto3.client('ec2').describe_regions()['Regions']))\n" | python | grep -v '^$(AWS_REGION)$$')

.PHONY: help deploy deploy-all-regions release clean test deploy-provider delete-provider demo delete-demo check_prefix

help:
	@echo 'make                    - builds a zip file to target/.'
	@echo 'make deploy             - deploy to the default region $(AWS_REGION).'
	@echo 'make deploy-all-regions - deploy to all regions.'
	@echo 'make release            - builds a zip file and deploys it to s3.'
	@echo 'make clean              - the workspace.'
	@echo 'make test               - execute the tests, requires a working AWS connection.'
	@echo 'make deploy-provider    - deploys the provider.'
	@echo 'make delete-provider    - deletes the provider.'
	@echo 'make demo               - deploys the demo cloudformation stack.'
	@echo 'make delete-demo        - deletes the demo cloudformation stack.'

deploy: target/$(NAME)-$(VERSION).zip
	aws s3 --region $(AWS_REGION) \
		cp --acl public-read \
		target/$(NAME)-$(VERSION).zip \
		s3://$(S3_BUCKET_PREFIX)-$(AWS_REGION)/lambdas/$(NAME)-$(VERSION).zip 
	aws s3 --region $(AWS_REGION) \
		cp --acl public-read \
		s3://$(S3_BUCKET_PREFIX)-$(AWS_REGION)/lambdas/$(NAME)-$(VERSION).zip \
		s3://$(S3_BUCKET_PREFIX)-$(AWS_REGION)/lambdas/$(NAME)-latest.zip 

deploy-all-regions: deploy
	@for REGION in $(ALL_REGIONS); do \
		echo "copying to region $$REGION.." ; \
		aws s3 --region $$REGION \
			cp  --acl public-read \
			s3://$(S3_BUCKET_PREFIX)-$(AWS_REGION)/lambdas/$(NAME)-$(VERSION).zip \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-$(VERSION).zip; \
		aws s3 --region $$REGION \
			cp  --acl public-read \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-$(VERSION).zip \
			s3://$(S3_BUCKET_PREFIX)-$$REGION/lambdas/$(NAME)-latest.zip; \
	done
		

do-push: deploy

do-build: target/$(NAME)-$(VERSION).zip

target/$(NAME)-$(VERSION).zip: src/*.py requirements.txt
	mkdir -p target
	docker build --build-arg ZIPFILE=$(NAME)-$(VERSION).zip -t $(NAME)-lambda:$(VERSION) -f Dockerfile.lambda . && \
		ID=$$(docker create $(NAME)-lambda:$(VERSION) /bin/true) && \
		docker export $$ID | (cd target && tar -xvf - $(NAME)-$(VERSION).zip) && \
		docker rm -f $$ID && \
		chmod ugo+r target/$(NAME)-$(VERSION).zip

venv: requirements.txt
	virtualenv -p python3 venv  && \
	. ./venv/bin/activate && \
	pip --quiet install --upgrade pip && \
	pip --quiet install -r requirements.txt 
	
clean:
	rm -rf venv target src/*.pyc tests/*.pyc

test: venv
	. ./venv/bin/activate && \
        python -m compileall src  && \
	pip --quiet install -r test-requirements.txt && \
	cd src && \
	PYTHONPATH=$(PWD)/src pytest ../tests/*.py

fmt:
	black src/*.py tests/*.py

deploy-provider: check_prefix
	aws --region $(AWS_REGION) cloudformation deploy \
		--capabilities CAPABILITY_IAM \
		--stack-name $(NAME) \
		--template-file ./cloudformation/cfn-resource-provider.yaml \
		--parameter-overrides LambdaS3Bucket=$(S3_BUCKET_PREFIX)-$(AWS_REGION) \
			CFNCustomProviderZipFileName=lambdas/$(NAME)-$(VERSION).zip

delete-provider:
	aws --region $(AWS_REGION) cloudformation delete-stack --stack-name $(NAME)
	aws --region $(AWS_REGION) cloudformation wait stack-delete-complete  --stack-name $(NAME)


demo:
	aws --region $(AWS_REGION) cloudformation deploy  --stack-name $(NAME)-demo \
		--capabilities CAPABILITY_IAM \
		--template-file ./cloudformation/demo-stack.yaml 

delete-demo:
	aws --region $(AWS_REGION) cloudformation delete-stack --stack-name $(NAME)-demo 
	aws --region $(AWS_REGION) cloudformation wait stack-delete-complete  --stack-name $(NAME)-demo

