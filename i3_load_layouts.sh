cat ~/i3/i3workspaces.txt | while read name; do
  i=`echo $name | cut -c1`
  i3-msg "workspace $name; append_layout ~/i3/i3layout_${i}.json"
done;

