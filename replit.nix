{pkgs}: {
  deps = [
    pkgs.nano
    pkgs.openssh
    pkgs.python311Packages.pytest
    pkgs.rustc
    pkgs.openssl
    pkgs.libiconv
    pkgs.cargo
    pkgs.tk
    pkgs.tcl
    pkgs.qhull
    pkgs.pkg-config
    pkgs.gtk3
    pkgs.gobject-introspection
    pkgs.ghostscript
    pkgs.freetype
    pkgs.ffmpeg-full
    pkgs.cairo
    pkgs.libxcrypt
    pkgs.google-cloud-sdk-gce
  ];
}
