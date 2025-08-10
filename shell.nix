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
  ];
  shellHook = ''
  '';
  env = {
    UV_PYTHON_DOWNLOADS = "never";
    UV_PYTHON = pythonPackages.python.interpreter;
  };
}

