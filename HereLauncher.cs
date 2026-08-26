using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("FFX Encoder Aqui")]
[assembly: System.Reflection.AssemblyCompany("DjManeca")]
[assembly: System.Reflection.AssemblyProduct("FFX Encoder")]
[assembly: System.Reflection.AssemblyVersion("3.0.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("3.0.0.0")]

internal static class HereLauncher
{
    [STAThread]
    private static void Main()
    {
        string installedExe = @"C:\FFX Encoder\FFX Encoder 3.0.exe";
        string targetDir = AppDomain.CurrentDomain.BaseDirectory
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);

        if (!File.Exists(installedExe))
        {
            MessageBox.Show(
                "FFX Encoder 3.0 nao encontrado.\n\nInstale primeiro em:\nC:\\FFX Encoder",
                "FFX Encoder Aqui",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            return;
        }

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = installedExe,
                Arguments = "\"" + targetDir + "\"",
                WorkingDirectory = targetDir,
                UseShellExecute = true,
                WindowStyle = ProcessWindowStyle.Normal
            };

            Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                "Falha ao iniciar o FFX Encoder.\n\n" + ex.Message,
                "FFX Encoder Aqui",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
        }
    }
}
