#!/usr/bin/env bash
# Extra simple script to update repo for Netflix CastagnaIt plugin
# v0.1.0
# by guindous
echo ">>> Delete old plugin version"
rm -Rf plugin.video.netflix
echo
echo ">>> Cloning project"
git clone https://github.com/CastagnaIT/plugin.video.netflix.git
echo
cd plugin.video.netflix/
lv=`git log --pretty=tformat:"%H %s" | egrep -i "version bump" | head -n 1`
vhash=`echo $lv | awk '{print $1}'`
vdesc=`echo $lv | awk '{first = $1; $1 = ""; print $0; }' | xargs`
vdesc="'$vdesc' (hash $vhash)"
echo ">>> Last version identified $vdesc"
cd ..
if git log --oneline | grep $vhash -q; then
	echo ">>> Already found this hash in published commit... exiting!"
	exit 1
fi
echo ">>> Restoring repo to version"
cd plugin.video.netflix/
git reset --hard $vhash
echo
echo ">>> Regenerate Kodi repository"
cd ..
python3 generator.py
echo
echo ">>> Publishing changes to git repo"
git add -A
git commit -m "Updating repo to $vdesc "
git push
echo ">>> Done!"
