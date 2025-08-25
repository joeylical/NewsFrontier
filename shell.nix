with import <nixpkgs> { };

let
  pythonPackages = python313Packages;
in pkgs.mkShell {
  name = "impurePythonEnv";
  buildInputs = [
    pythonPackages.python
    pkgs.uv
    pkgs.ruff
    pkgs.pnpm
    pkgs.libz
    pkgs.stdenv.cc.cc.lib
  ];
  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath ([
      pkgs.libz
      pkgs.stdenv.cc.cc
    ])}
    sudo nixos-firewall-tool open tcp 3000
  '';
  env = {
    UV_PYTHON_DOWNLOADS = "never";
    UV_PYTHON = pythonPackages.python.interpreter;
  };
}

