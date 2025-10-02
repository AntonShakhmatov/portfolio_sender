<?php

namespace App\Model\Services;

use Smalot\PdfParser\Parser as Smalot;
use Symfony\Component\Process\Process;

final class PdfTextExtractor{
    public function __construct(private bool $preferPdfToText = true)
    {
        
    }

    public function extract(string $path)
    {
        if(!is_file($path)){
            throw new \RuntimeException("PDF not found: $path");
        }

        if($this->preferPdfToText && trim(shell_exec('which pdftotext')) !== ''){
            $cmd = ['pdftotext', '-layout', '-enc', 'UTF-8', $path, '-'];
            $p = new Process($cmd);
            $p->run();
            if($p->isSuccessful()){
                $out = $p->getOutput();
                if (mb_strlen(trim($out)) > 0) return $out;
            }
        }

        $parser = new Smalot();
        $pdf = $parser->parseFile($path);
        return $pdf->getText();
    }

    public function ocrIfNeeded(string $path)
    {
        if (trim($this->extract($path)) !== '') return null;
        return null;
    }
}