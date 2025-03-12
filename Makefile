SOURCE = example/main.cpp

build/report.pdf: build/report.tex
	cd build && pdflatex -interaction=nonstopmode -shell-escape report.tex

build/report.tex: build/main $(SOURCE)
	./reportify.py $(SOURCE) build/main > build/report.tex

build/main: build $(SOURCE) 
	g++ -o build/main $(SOURCE)

build:
	mkdir -p build
