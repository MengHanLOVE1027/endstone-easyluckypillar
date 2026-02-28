cd ~\Desktop\Plugins-Dev\EndStone\Projects\endstone-easyluckypillar\
Remove-Item '.\dist\*' -Recurse
Remove-Item '.\build\*' -Recurse
Remove-Item '.\src\endstone_easyluckypillar.egg-info' -Recurse
python .\setup.py sdist build
pipx run build --wheel
cd ~\Desktop\Plugins-Dev\Endstone\
Remove-Item 'C:\Users\HeYuHan\Desktop\Plugins-Dev\Endstone\bedrock_server\plugins\endstone_easyluckypillar*.whl'
Copy-Item -Path 'C:\Users\HeYuHan\Desktop\Plugins-Dev\EndStone\Projects\endstone-easyluckypillar\dist\end*.whl' -Destination 'C:\Users\HeYuHan\Desktop\Plugins-Dev\Endstone\bedrock_server\plugins'
# cls
start .\start.cmd