#!/bin/bash

desktop_dir=$(realpath `dirname $0`)
cd ${desktop_dir}/..
home=`pwd`

echo Install-Dir = ${home}

for template in ${desktop_dir}/*.desktop
do
    file=`basename $template`
    # Sed will take any char as separator
    # use | since filenames use /
    sed "s|@@home|${home}|" $template > ~/Desktop/${file}
done

