#!/bin/bash

RELEASE_FILE='./build/Releasenotes.txt'
COMMIT_FILE='./build/Commits.txt'

printf '<Summary>\n\n' > $RELEASE_FILE
printf 'New Features\n\n\n' >> $RELEASE_FILE
printf 'Improvements\n\n\n' >> $RELEASE_FILE
printf 'Bugfixes\n\n\n' >> $RELEASE_FILE
printf 'Documentation\n\n\n' >> $RELEASE_FILE

git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:%s > $COMMIT_FILE
sed -i 's/^/ - /' $COMMIT_FILE

cat $COMMIT_FILE >> $RELEASE_FILE
rm $COMMIT_FILE

git tag -a $1 --edit --file $RELEASE_FILE