on run
	my interactiveLaunch()
end run

on open droppedItems
	set targetPaths to {}
	repeat with droppedItem in droppedItems
		set end of targetPaths to POSIX path of droppedItem
	end repeat
	my runTargets(targetPaths)
end open

on interactiveLaunch()
	set projectRoot to my projectRootPOSIX()
	set actionChoices to {"选择单个 JSON 出图", "选择整个文件夹批量出图", "打开输出目录", "打开 JSON 目录", "打开 AI 模板"}
	set picked to choose from list actionChoices with prompt "请选择你要做的事：" default items {"选择单个 JSON 出图"}
	if picked is false then
		return
	end if

	set actionName to item 1 of picked
	if actionName is "选择单个 JSON 出图" then
		set pickedFile to choose file with prompt "请选择一个 JSON 文件："
		my runTargets({POSIX path of pickedFile})
	else if actionName is "选择整个文件夹批量出图" then
		set pickedFolder to choose folder with prompt "请选择一个包含 JSON 的文件夹："
		my runTargets({POSIX path of pickedFolder})
	else if actionName is "打开输出目录" then
		do shell script "open " & quoted form of (projectRoot & "/xhs-render/output")
	else if actionName is "打开 JSON 目录" then
		do shell script "open " & quoted form of (projectRoot & "/json")
	else if actionName is "打开 AI 模板" then
		do shell script "open " & quoted form of (projectRoot & "/xhs-render/ai_json_prompt_template.txt")
	end if
end interactiveLaunch

on runTargets(targetPaths)
	if (count of targetPaths) is 0 then
		return
	end if

	set projectRoot to my projectRootPOSIX()
	set xhsRoot to projectRoot & "/xhs-render"
	set cliPath to xhsRoot & "/easy_render_cli.py"
	set shellCommand to "export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin; cd " & quoted form of xhsRoot & "; python3 " & quoted form of cliPath

	repeat with targetPath in targetPaths
		set shellCommand to shellCommand & " " & quoted form of (targetPath as text)
	end repeat

	display notification "正在出图，请稍等…" with title "小红书本地排版"
	try
		do shell script shellCommand
		display notification "出图完成，结果目录已自动打开。" with title "小红书本地排版"
	on error errMsg number errNum
		display alert "出图失败" message errMsg as warning buttons {"好"} default button "好"
	end try
end runTargets

on projectRootPOSIX()
	set mePath to POSIX path of (path to me)
	set baseDir to do shell script "dirname " & quoted form of mePath

	try
		do shell script "test -d " & quoted form of (baseDir & "/xhs-render")
		return baseDir
	on error
		return do shell script "dirname " & quoted form of baseDir
	end try
end projectRootPOSIX
