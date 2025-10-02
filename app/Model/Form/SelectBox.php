<?php

namespace App\Model\Form;

class SelectBox extends \Nette\Forms\Controls\SelectBox
{
    public function isOptionDisabled($optionValue): bool
    {
        return is_array($this->disabled) && isset($this->disabled[$optionValue]);
    }

    public function getDisabled()
    {
        return $this->disabled;
    }
}