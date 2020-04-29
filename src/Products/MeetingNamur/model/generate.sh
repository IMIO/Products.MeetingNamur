#!/bin/sh
/srv/archgenxml/bin/archgenxml --cfg generate.conf MeetingNamur.zargo -o tmp

# only keep workflows
cp -rf tmp/profiles/default/workflows/meetingnamur_workflow ../profiles/default/workflows
cp -rf tmp/profiles/default/workflows/meetingitemnamur_workflow ../profiles/default/workflows
rm -rf tmp
