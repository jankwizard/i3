for i in `seq 0 9`; do
  mkdir -p ~/i3/
  i3-save-tree --workspace $i | tail -n +2 | fgrep -v '// split' | sed 's|// "class| "class|g' | sed 's|//.*||g' | sed 's|\(class.*\),|\1|g' > ~/i3/i3layout_${i}.json
  i3-msg -t get_workspaces | jq '.[] | .name'   | cut -d"\"" -f2 > ~/i3/i3workspaces.txt
done;

