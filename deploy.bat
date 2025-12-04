@echo off
echo === Building Frontend ===
cd frontend
call npm run build
cd ..

echo === Copying to Backend ===
rmdir /S /Q backend\static 2>nul
xcopy /E /I /Y frontend\dist backend\static

echo === Committing ===
git add .
git commit -m "Deploy: %date% %time%"
git push origin main

echo === Done! ===
pause