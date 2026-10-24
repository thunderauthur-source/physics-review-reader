using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

class Program
{
    const string AppVersion = "1.0";
    const string RegPath = @"Software\物理复习提纲阅读器";

    [STAThread]
    static void Main(string[] args)
    {
        bool silent = false;
        bool setup = false;
        bool extractOnly = false;
        string onlyDir = null;
        string overrideTarget = null;
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--silent") silent = true;
            else if (args[i] == "--setup") setup = true;
            else if (args[i] == "--extract-only" && i + 1 < args.Length)
            {
                extractOnly = true;
                onlyDir = args[++i];
            }
            else if (args[i] == "--target" && i + 1 < args.Length)
            {
                overrideTarget = args[++i];
            }
        }

        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        if (extractOnly)
        {
            try { Extract(Path.GetFullPath(onlyDir), null); }
            catch (Exception ex) { Log("extract-only fail: " + ex); }
            return;
        }

        string remembered = ReadInstallPath();
        if (!setup && overrideTarget == null && remembered != null && IsInstalled(remembered))
        {
            Launch(Path.Combine(remembered, "程序", "QMLauncher.exe"));
            return;
        }

        if (silent)
        {
            string target = overrideTarget != null
                ? Path.GetFullPath(overrideTarget)
                : (remembered != null && Directory.Exists(remembered) ? remembered : DefaultDir());
            try
            {
                Extract(target, null);
                Program.CreateShortcut(target);
                WriteInstallPath(target);
                Launch(Path.Combine(target, "程序", "QMLauncher.exe"));
            }
            catch (Exception ex) { Log("silent fail: " + ex); }
            return;
        }

        string initial = overrideTarget != null
            ? Path.GetFullPath(overrideTarget)
            : (remembered != null && Directory.Exists(remembered) ? remembered : DefaultDir());

        SetupForm form = new SetupForm(initial);
        Application.Run(form);
        if (form.Success)
        {
            Launch(Path.Combine(form.InstallPath, "程序", "QMLauncher.exe"));
        }
    }

    static string DefaultDir()
    {
        if (Directory.Exists(@"D:\"))
            return @"D:\物理复习提纲阅读器";
        return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "物理复习提纲阅读器");
    }

    static bool IsInstalled(string dir)
    {
        try
        {
            return File.Exists(Path.Combine(dir, "程序", "QMLauncher.exe")) &&
                   File.Exists(Path.Combine(dir, "version.txt"));
        }
        catch { return false; }
    }

    static string ReadInstallPath()
    {
        try
        {
            using (RegistryKey k = Registry.CurrentUser.OpenSubKey(RegPath))
            {
                if (k == null) return null;
                string p = k.GetValue("InstallPath") as string;
                return string.IsNullOrEmpty(p) ? null : p;
            }
        }
        catch { return null; }
    }

    internal static void WriteInstallPath(string dir)
    {
        try
        {
            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(RegPath))
            {
                k.SetValue("InstallPath", dir);
                k.SetValue("Version", AppVersion);
            }
        }
        catch (Exception ex) { Log("registry fail: " + ex); }
    }

    internal static void Log(string msg)
    {
        try
        {
            File.AppendAllText(Path.Combine(Path.GetTempPath(), "physreader_bootstrap.log"),
                DateTime.Now.ToString("s") + " " + msg + Environment.NewLine);
        }
        catch { }
    }

    static bool IsSkipped(string name)
    {
        string n = name.Replace('\\', '/');
        int idx = n.IndexOf('/');
        string rel = idx >= 0 ? n.Substring(idx + 1) : n;
        return rel.StartsWith("程序/edgeprofile/", StringComparison.OrdinalIgnoreCase);
    }

    internal static void Extract(string target, Action<string, int> progress)
    {
        Directory.CreateDirectory(target);
        string root = Path.GetFullPath(target) + Path.DirectorySeparatorChar;

        using (Stream stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("payload.zip"))
        {
            if (stream == null) throw new Exception("安装包资源缺失。");
            using (ZipArchive zip = new ZipArchive(stream, ZipArchiveMode.Read))
            {
                long total = 0;
                foreach (ZipArchiveEntry e in zip.Entries)
                {
                    if (!IsSkipped(e.FullName)) total += e.Length;
                }
                long done = 0;
                foreach (ZipArchiveEntry e in zip.Entries)
                {
                    string name = e.FullName.Replace('\\', '/');
                    int idx = name.IndexOf('/');
                    string rel = idx >= 0 ? name.Substring(idx + 1) : name;
                    if (rel.Length == 0) continue;
                    if (rel.StartsWith("程序/edgeprofile/", StringComparison.OrdinalIgnoreCase)) continue;

                    string dest = Path.GetFullPath(Path.Combine(target, rel.Replace('/', Path.DirectorySeparatorChar)));
                    if (!dest.StartsWith(root, StringComparison.OrdinalIgnoreCase)) continue;

                    if (rel.EndsWith("/"))
                    {
                        Directory.CreateDirectory(dest);
                        continue;
                    }

                    Directory.CreateDirectory(Path.GetDirectoryName(dest));
                    e.ExtractToFile(dest, true);
                    done += e.Length;
                    int pct = total > 0 ? (int)(done * 100 / total) : 0;
                    if (progress != null) progress("正在复制文件… " + pct + "%", pct);
                }
            }
        }
        File.WriteAllText(Path.Combine(target, "version.txt"), AppVersion);
    }

    internal static void CreateShortcut(string target)
    {
        try
        {
            string exe = Path.Combine(target, "程序", "QMLauncher.exe");
            string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            Type shellType = Type.GetTypeFromProgID("WScript.Shell");
            if (shellType == null) return;
            dynamic shell = Activator.CreateInstance(shellType);
            dynamic sc = shell.CreateShortcut(Path.Combine(desktop, "物理复习提纲阅读器.lnk"));
            sc.TargetPath = exe;
            sc.WorkingDirectory = Path.GetDirectoryName(exe);
            sc.IconLocation = exe + ",0";
            sc.Description = "物理复习提纲阅读器";
            sc.Save();
        }
        catch (Exception ex) { Log("shortcut fail: " + ex); }
    }

    static void Launch(string exe)
    {
        try
        {
            if (!File.Exists(exe)) return;
            ProcessStartInfo psi = new ProcessStartInfo(exe);
            psi.WorkingDirectory = Path.GetDirectoryName(exe);
            psi.UseShellExecute = true;
            Process.Start(psi);
        }
        catch (Exception ex) { Log("launch fail: " + ex); }
    }
}

class SetupForm : Form
{
    TextBox pathBox;
    Button browseBtn;
    Button installBtn;
    Button cancelBtn;
    ProgressBar bar;
    Label status;
    bool installing;

    public string InstallPath;
    public bool Success;

    public SetupForm(string initial)
    {
        Text = "安装 物理复习提纲阅读器";
        Width = 610;
        Height = 280;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        StartPosition = FormStartPosition.CenterScreen;
        MaximizeBox = false;
        MinimizeBox = false;
        ShowInTaskbar = true;

        Label title = new Label();
        title.Text = "选择安装位置";
        title.Font = new System.Drawing.Font("Microsoft YaHei UI", 13F, System.Drawing.FontStyle.Bold);
        title.SetBounds(22, 16, 300, 30);
        Controls.Add(title);

        Label hint = new Label();
        hint.Text = "建议装在非系统盘（如 D:\\物理复习提纲阅读器）。安装后会在桌面创建快捷方式。";
        hint.SetBounds(22, 48, 550, 22);
        hint.ForeColor = System.Drawing.Color.FromArgb(90, 90, 90);
        Controls.Add(hint);

        pathBox = new TextBox();
        pathBox.Text = initial;
        pathBox.SetBounds(22, 80, 440, 26);
        Controls.Add(pathBox);

        browseBtn = new Button();
        browseBtn.Text = "浏览…";
        browseBtn.SetBounds(472, 79, 85, 28);
        browseBtn.Click += delegate { Browse(); };
        Controls.Add(browseBtn);

        Label note = new Label();
        note.Text = "阅读进度、书签、笔记都保存在安装目录里；重装/升级会保留。";
        note.SetBounds(22, 114, 550, 22);
        note.ForeColor = System.Drawing.Color.FromArgb(110, 110, 110);
        Controls.Add(note);

        bar = new ProgressBar();
        bar.SetBounds(22, 146, 535, 18);
        bar.Minimum = 0;
        bar.Maximum = 100;
        bar.Visible = false;
        Controls.Add(bar);

        status = new Label();
        status.SetBounds(22, 170, 535, 22);
        status.ForeColor = System.Drawing.Color.FromArgb(70, 120, 105);
        Controls.Add(status);

        installBtn = new Button();
        installBtn.Text = "开始安装";
        installBtn.SetBounds(372, 202, 100, 30);
        installBtn.Click += delegate { StartInstall(); };
        Controls.Add(installBtn);

        cancelBtn = new Button();
        cancelBtn.Text = "取消";
        cancelBtn.SetBounds(482, 202, 75, 30);
        cancelBtn.Click += delegate { Close(); };
        Controls.Add(cancelBtn);

        AcceptButton = installBtn;
        CancelButton = cancelBtn;
    }

    void Browse()
    {
        using (FolderBrowserDialog dlg = new FolderBrowserDialog())
        {
            dlg.Description = "选择安装文件夹";
            dlg.SelectedPath = pathBox.Text;
            if (dlg.ShowDialog(this) == DialogResult.OK)
                pathBox.Text = dlg.SelectedPath;
        }
    }

    string Normalize(string input)
    {
        string p = (input ?? "").Trim().Trim('"');
        if (p.Length == 0) throw new Exception("请填写安装位置。");
        p = Path.GetFullPath(p);
        string root = Path.GetPathRoot(p);
        if (root != null && p.TrimEnd('\\').Equals(root.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase))
            p = Path.Combine(p, "物理复习提纲阅读器");
        return p;
    }

    void StartInstall()
    {
        if (installing) return;
        string target;
        try { target = Normalize(pathBox.Text); }
        catch (Exception ex)
        {
            MessageBox.Show(this, ex.Message, "安装位置", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        try
        {
            Directory.CreateDirectory(target);
            string probe = Path.Combine(target, ".write_test_" + Guid.NewGuid().ToString("N") + ".tmp");
            File.WriteAllText(probe, "x");
            File.Delete(probe);
        }
        catch (Exception ex)
        {
            MessageBox.Show(this, "这个位置不能写入：\n" + target + "\n\n" + ex.Message +
                "\n\n请换一个文件夹，或选择 D 盘。", "安装位置不可用",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }

        bool hasApp = File.Exists(Path.Combine(target, "程序", "QMLauncher.exe"));
        bool exists = Directory.Exists(target) && Directory.GetFileSystemEntries(target).Length > 0;
        if (exists)
        {
            string msg = hasApp
                ? "该目录已经安装过阅读器。\n继续会覆盖程序文件，但保留阅读进度、书签和笔记。\n\n继续安装吗？"
                : "该目录不是空的。\n继续会把阅读器文件写入这个目录。\n\n继续吗？";
            if (MessageBox.Show(this, msg, "确认安装", MessageBoxButtons.YesNo,
                    MessageBoxIcon.Question) != DialogResult.Yes)
                return;
        }

        InstallPath = target;
        installing = true;
        pathBox.Enabled = false;
        browseBtn.Enabled = false;
        installBtn.Enabled = false;
        cancelBtn.Enabled = false;
        bar.Visible = true;
        status.Text = "正在准备…";

        Thread th = new Thread(delegate()
        {
            try
            {
                Program.Extract(target, SetStatus);
                SetStatus("正在创建桌面快捷方式…", 100);
                Program.CreateShortcut(target);
                Program.WriteInstallPath(target);
                Success = true;
                BeginInvoke((Action)delegate
                {
                    installing = false;
                    Close();
                });
            }
            catch (Exception ex)
            {
                Program.Log("setup fail: " + ex);
                BeginInvoke((Action)delegate
                {
                    installing = false;
                    pathBox.Enabled = true;
                    browseBtn.Enabled = true;
                    installBtn.Enabled = true;
                    cancelBtn.Enabled = true;
                    bar.Visible = false;
                    status.Text = "";
                    MessageBox.Show(this, "安装失败：\n" + ex.Message +
                        "\n\n请关闭可能占用文件的阅读器窗口后重试，或换一个安装位置。",
                        "安装失败", MessageBoxButtons.OK, MessageBoxIcon.Error);
                });
            }
        });
        th.IsBackground = true;
        th.SetApartmentState(ApartmentState.STA);
        th.Start();
    }

    public void SetStatus(string text, int percent)
    {
        if (InvokeRequired)
        {
            BeginInvoke((Action)delegate { SetStatus(text, percent); });
            return;
        }
        status.Text = text;
        bar.Value = Math.Max(0, Math.Min(100, percent));
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        if (installing && e.CloseReason == CloseReason.UserClosing)
        {
            e.Cancel = true;
            return;
        }
        base.OnFormClosing(e);
    }
}
