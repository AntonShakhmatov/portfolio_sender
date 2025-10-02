<?php

namespace App\Forms;

use Nette;
use Nette\Application\UI\Form;

final class UploadFormFactory
{
    public function __construct(private string $wwwDir) {}

    public function create(callable $onSuccess): Form
    {
        $form = new Form;
        $form->addProtection();

        $form->addUpload('file', 'Soubor')
            ->setRequired('Vyberte soubor.')
            ->addRule(Form::MAX_FILE_SIZE, 'Max. 2 MB.', 2 * 1024 * 1024)
            ->addRule(Form::MIME_TYPE, 'Povoleno: PDF nebo ZIP.', [
                'application/pdf', 'application/zip',
            ]);

        $form->addSubmit('send', 'Uložit');

        $form->onSuccess[] = function (Form $form, \stdClass $v) use ($onSuccess): void {
            $uploadDir = rtrim($this->wwwDir, '/\\') . '/uploads';

            \Nette\Utils\FileSystem::createDir($uploadDir, 0775);
            if (!is_writable($uploadDir)) {
                $form->addError("Složka není zapisovatelná: $uploadDir");
                return;
            }

            /** @var \Nette\Http\FileUpload $file */
            $file = $v->file;
            if (!$file->isOk()) {
                $form->addError(self::uploadErr($file->getError()));
                return;
            }

            $orig = $file->getName() ?: 'soubor';
            $base = pathinfo($orig, PATHINFO_FILENAME);
            $name = \extension_loaded('intl')
                ? \Nette\Utils\Strings::webalize($base) ?: 'file'
                : (strtolower(trim(preg_replace('~[^A-Za-z0-9]+~', '-', @iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$base) ?: $base), '-')) ?: 'file');

            $ext  = strtolower((string) pathinfo($orig, PATHINFO_EXTENSION));
            $target = $uploadDir . '/' . $name . '-' . \Nette\Utils\Random::generate(8) . ($ext ? ".$ext" : '');

            try {
                $file->move($target);
            } catch (\Throwable $e) {
                $form->addError('Nepodařilo se uložit soubor: ' . $e->getMessage());
                return;
            }

            $presenter = $form->getPresenter();
            $section = $presenter->getSession('upload');
            $section->lastFile = basename($target);
        
            $req = $presenter->getHttpRequest();
            $wantsJson = $presenter->isAjax()
                || stripos((string)$req->getHeader('X-Requested-With'), 'XMLHttpRequest') !== false
                || (strpos((string)$req->getHeader('Accept'), 'application/json') !== false);
        
            if ($wantsJson) {
                $presenter->sendJson([
                    'ok'       => true,
                    'filename' => basename($target),
                    'message'  => 'Soubor uložen.',
                    'redirect' => $presenter->link('Homepage:create'),
                    // 'redirect' => $presenter->link('this'),
                ]);
                return;
            }
            $onSuccess();
        };

        return $form;
    }

    private static function uploadErr(int $code): string
    {
        return match ($code) {
            \UPLOAD_ERR_INI_SIZE    => 'Soubor překročil upload_max_filesize.',
            \UPLOAD_ERR_FORM_SIZE   => 'Soubor překročil MAX_FILE_SIZE.',
            \UPLOAD_ERR_PARTIAL     => 'Soubor byl nahrán jen částečně.',
            \UPLOAD_ERR_NO_FILE     => 'Nebyl vybrán žádný soubor.',
            \UPLOAD_ERR_NO_TMP_DIR  => 'Chybí dočasná složka (upload_tmp_dir).',
            \UPLOAD_ERR_CANT_WRITE  => 'Nelze zapsat soubor na disk (práva).',
            \UPLOAD_ERR_EXTENSION   => 'Nahrávání zastaveno rozšířením PHP.',
            default                 => 'Neznámá chyba nahrávání.',
        };
    }
}
