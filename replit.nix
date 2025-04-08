{pkgs}: {
  deps = [
    pkgs.sqlite
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
