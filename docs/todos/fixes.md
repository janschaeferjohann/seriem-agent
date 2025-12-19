# Electron build - done
Now run these steps in order:
Step 1: Build the Angular frontend first
cd C:\work\git\github\seriem-agent\frontendnpm run build
Step 2: Clear the electron-builder cache (fixes the symlink issue)
cd C:\work\git\github\seriem-agent\frontendnpm run build
Step 3: Build the Electron app
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache\winCodeSign" -ErrorAction SilentlyContinue
The signAndEditExecutable: false setting I added will skip code signing, which avoids the symlink permission issue entirely for unsigned dev builds.