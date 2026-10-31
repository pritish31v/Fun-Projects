def steam_installed_games():
    roots = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam",
             os.path.expanduser("~/.local/share/Steam"),
             os.path.expanduser("~/Library/Application Support/Steam")]
    libs = set()
    for root in roots:
        libs.add(os.path.join(root, "steamapps"))
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            with open(vdf, encoding="utf-8", errors="ignore") as f:
                for p in re.findall(r'"path"\s+"([^"]+)"', f.read()):
                    libs.add(os.path.join(p.replace("\\\\", "\\"), "steamapps"))
    names = set()
    for lib in libs:
        for acf in glob.glob(os.path.join(lib, "appmanifest_*.acf")):
            with open(acf, encoding="utf-8", errors="ignore") as f:
                m = re.search(r'"name"\s+"([^"]+)"', f.read())
            if m and not re.search(r"Steamworks|Redistributable|Proton", m.group(1)):
                names.add(m.group(1))
    return sorted(names)
