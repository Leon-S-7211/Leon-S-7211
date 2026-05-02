@echo off
chcp 65001 >nul
REM =============================================================
REM  直播监控守护进程 - 开机自启脚本
REM
REM  部署: Win+R → shell:startup → 把这个 .bat 的快捷方式拖进去
REM =============================================================

set PROJECT_DIR=D:\douyin-to-text

cd /d %PROJECT_DIR%

echo ============================================================
echo   Douyin-to-Text 直播监控
echo   项目: %PROJECT_DIR%
echo   时间: %date% %time%
echo ============================================================
echo.
echo   关闭窗口或 Ctrl+C 停止
echo.

python -u -m src.live

echo.
echo [警告] 监控已停止
pause
