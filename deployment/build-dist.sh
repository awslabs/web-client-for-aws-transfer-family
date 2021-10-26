#!/bin/bash
#
# This assumes  git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./build-dist.sh source-bucket-base-name solution-name version-code
#
# Parameters:
#  - source-bucket-base-name: Name for the S3 bucket location where the template will source the Lambda
#    code from. The template will append '-[region_name]' to this bucket name.
#    For example: ./build-dist.sh solutions web-client-for-aws-transfer-family v1.0.0
#    The template will then expect the lambda source code to be located in the solutions-[region_name] bucket
#
#  - solution-name: name of the solution for consistency
#
#  - version-code: version of the package

# Check to see if input has been provided:
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide the base source bucket name, trademark approved solution name and version where the lambda code will eventually reside."
    echo "For example: ./build-dist.sh solutions web-client-for-aws-transfer-family v1.0.0
"
    exit 1
fi

# Get reference for all important folders
deployment_dir="$PWD"
dist_dir="dist"
cd ..
root_dir=$PWD
echo $root_dir

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist folders and create a new one"
echo "------------------------------------------------------------------------------"
echo "rm -rf $dist_dir"
rm -rf $dist_dir

echo "mkdir -p $dist_dir"
mkdir -p $dist_dir

echo "------------------------------------------------------------------------------"
echo "[Packing] Copy local repo to $dist_dir"
echo "------------------------------------------------------------------------------"
#cp -R $root_dir/ $dist_dir/
rsync -a --exclude $dist_dir --exclude .git $root_dir/ $dist_dir

echo "------------------------------------------------------------------------------"
echo "Updating code source bucket in template with $1"
echo "------------------------------------------------------------------------------"
if [[ "$OSTYPE" == "darwin"* ]]; then
  replace="s/%%BUCKET_NAME%%/$1/g"
  echo "sed -i '' -e $replace $dist_dir/deployment/*.template"
  sed -i '' -e $replace $dist_dir/deployment/*.template
  replace="s/%%SOLUTION_NAME%%/$2/g"
  echo "sed -i '' -e $replace $dist_dir/deployment/*.template"
  sed -i '' -e $replace $dist_dir/deployment/*.template
  replace="s/%%VERSION%%/$3/g"
  echo "sed -i '' -e $dist_dir/deployment/*.template"
  sed -i '' -e $replace $dist_dir/deployment/*.template
else
  replace="s/%%BUCKET_NAME%%/$1/g"
  echo "sed -i -e $replace $dist_dir/deployment/*.template"
  sed -i -e $replace $dist_dir/deployment/*.template
  replace="s/%%SOLUTION_NAME%%/$2/g"
  echo "sed -i -e $replace $dist_dir/deployment/*.template"
  sed -i -e $replace $dist_dir/deployment/*.template
  replace="s/%%VERSION%%/$3/g"
  echo "sed -i -e $dist_dir/deployment/*.template"
  sed -i -e $replace $dist_dir/deployment/*.template
fi