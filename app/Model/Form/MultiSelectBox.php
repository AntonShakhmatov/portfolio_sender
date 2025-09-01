<?php

namespace App\Model\Form;

class MultiSelectBox extends \Nette\Forms\Controls\MultiSelectBox
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