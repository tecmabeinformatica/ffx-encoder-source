using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("FFX Encoder 3.0 Launcher")]
[assembly: System.Reflection.AssemblyCompany("DjManeca")]
[assembly: System.Reflection.AssemblyProduct("FFX Encoder")]
[assembly: System.Reflection.AssemblyVersion("3.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("3.0.0.0")]

internal static class Launcher
{
    [STAThread]
    private static void Main(string[] args)
    {
        string appDir = AppDomain.CurrentDomain.BaseDirectory
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string mainScript = Path.Combine(appDir, "main.py");

        if (!File.Exists(mainScript))
        {
            MessageBox.Show(
                "main.py nao foi encontrado.\n\n" + mainScript,
                "FFX Encoder",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return;
        }

        string targetDir = args.Length > 0 && !string.IsNullOrWhiteSpace(args[0])
            ? args[0].Trim()
            : appDir;

        string command = string.Format(
            "title FFX Encoder 3.0 && python \"{0}\" \"{1}\" && exit /b %errorlevel%",
            mainScript,
            targetDir);

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "cmd.exe",
                Arguments = "/c \"" + command + "\"",
                WorkingDirectory = appDir,
                UseShellExecute = true,
                WindowStyle = ProcessWindowStyle.Normal
            };

            Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                "Falha ao iniciar o FFX Encoder.\n\n" + ex.Message,
                "FFX Encoder",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
        }
    }
}
