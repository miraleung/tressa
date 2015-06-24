#!/bin/bash
DIVIDER = "======================================"
HRULE = "+++++++++++++++"

info_print(){
  if [[ $1 != "" ]]; then
    echo $DIVIDER
    echo "$HRULE $1 $HRULE"
    echo $DIVIDER
  fi
  return 0
}

info_print "MAKEING TRESSA"
make \
  && info_print "TRESSA DONE; MAKEING LLVM" \
  && cd ~/llvm \
  && ./llvm-make.sh \
  && info_print "LLVM MAKE DONE; INSTALLING LLVM" \
  && ./llvm-install.sh \
  && info_print "LLVM INSTALL DONE"

if [[ $1 != "" && $1 == "-x" ]]; then
  info_print "MAKEING XEN"
  cd ~/xen-unstable.hg
  ./xen-make.sh
fi
