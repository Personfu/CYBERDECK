# Latexmk config for CI and local builds
$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
$clean_ext = 'aux bbl blg idx ind lof lot out toc fls fdb_latexmk synctex.gz';
