{
    description = "Flake for Numerical Methods";

    inputs.flake-utils.url = "github:numtide/flake-utils";

    outputs = { nixpkgs, flake-utils, ... }:
        flake-utils.lib.eachDefaultSystem (system:
            let
                pkgs = nixpkgs.legacyPackages.${system};
            in
            {
                devShells.default = pkgs.mkShell {
                    buildInputs = [];

                    env = {
                        CPATH = builtins.concatStringsSep ":" [
                            (pkgs.stdenv.cc.cc + "/include/c++/13.2.0")
                        ];
                        LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
                            pkgs.stdenv.cc.cc.lib
                        ];
                    };
                };
            }
        );
}
