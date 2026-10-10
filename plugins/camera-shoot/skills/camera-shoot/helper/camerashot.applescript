-- CameraShot helper (macOS): a tiny app that owns the camera permission for the
-- camera-shoot skill, for agent hosts whose own process can't get a camera grant.
--
-- It reads one command line from the "args" file next to the app, runs it, and
-- writes all output to "out.log" next to the app. The command must start with
-- imagesnap or ffmpeg and contain no shell metacharacters; anything else is refused.
--
-- Build: osacompile -o "<dir>/CameraShot.app" camerashot.applescript
on run
	set appPath to POSIX path of (path to me)
	set baseDir to do shell script "dirname " & quoted form of appPath
	set argsFile to baseDir & "/args"
	set logFile to baseDir & "/out.log"
	try
		set cmdLine to do shell script "cat " & quoted form of argsFile
	on error
		do shell script "echo 'CameraShot: no args file at '" & quoted form of argsFile & " > " & quoted form of logFile
		return
	end try
	set firstWord to do shell script "printf '%s' " & quoted form of cmdLine & " | awk '{print $1}'"
	if firstWord is not in {"imagesnap", "ffmpeg"} then
		do shell script "echo 'CameraShot: refused, command must start with imagesnap or ffmpeg'" & " > " & quoted form of logFile
		return
	end if
	repeat with c in {";", "&", "|", "`", "$", "<", ">", "(", ")"}
		if cmdLine contains (c as text) then
			do shell script "echo 'CameraShot: refused, shell metacharacters are not allowed in args'" & " > " & quoted form of logFile
			return
		end if
	end repeat
	try
		do shell script "export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin; " & cmdLine & " > " & quoted form of logFile & " 2>&1"
	on error errMsg
		do shell script "echo " & quoted form of errMsg & " >> " & quoted form of logFile
	end try
end run
