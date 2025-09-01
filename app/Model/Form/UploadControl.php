<?php

namespace App\Model\Form;


class UploadControl extends \Nette\Forms\Controls\UploadControl
{
    private $fileName;

    /**
     * @return \Nette\Forms\Controls\UploadControl
     * @internal
     */
    public function setValue($value)
    {
        $this->fileName = $value;
        return $this;
    }

    public function getFileName()
    {
        return $this->fileName;
    }
}