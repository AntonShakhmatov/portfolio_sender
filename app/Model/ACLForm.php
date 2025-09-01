<?php

namespace App\Model;

use App\Model\Form\MultiSelectBox;
use App\Model\Form\SelectBox;
use App\Model\Form\UploadControl;
use Nette\Application\UI;
use App\Model\Database\Entity\PermissionItem;
use Nette\Security\User;

class ACLForm extends UI\Form
{

    /** @var User */
    private $user;

    /** @var string */
    private $namePresenter;

    /** @var ACLMapper */
    private $mapper;

    /** @var string */
    private $nameForm;

    /** array of foreign entity for save method */
    public $arrayForeignEntity = NULL;

    /** array of foreign entity whit N:N for save method */
    public $arrayNNForeignEntity = NULL;

    /** messages on success form */
    public $messageOk;

    /** messages on error form */
    public $messageEr;

    /** target to redirect on success */
    public $target;

    /** redirect after save? */
    public $isRedirect = true;

    /** target parameters */
    public $targetPar;

    /** class in form */
    public $class;

    public array $sections = [];
    public array $sectionProperties = [];
    public array $propertiesColumn = [];

    public array $filesPath = [];

    public array $filesPrefix = [];

    /**
     * Set scope for ACL mapping
     * @param User $user login user identity
     * @param string $presenter name of destination presenter
     * @param string $function name of destination function / form
     * @param ACLMapper $mapper
     * @throws \Exception
     */
    public function setScope($user, $presenter, $function, $mapper)
    {
        $this->user = $user;
        $this->namePresenter = $presenter;
        $this->nameForm = $function;
        $this->mapper = $mapper;
        $this->mapper->mapFunction(NULL, $user, $presenter, $function, PermissionItem::TYPE_FORM);
    }

    /**
     * @param $name
     * @param null $label
     * @param null $cols
     * @param null $maxLength
     * @return \Nette\Forms\Controls\TextInput|null
     * @throws \Exception
     */
    public function addTextAcl($name, $label = NULL, $cols = NULL, $maxLength = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addText($name, $label, $cols, $maxLength);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * Adds select box control that allows single item selection.
     * @param  string|object  $label
     */
    public function addSelect(string $name, $label = null, array $items = null, int $size = null): SelectBox
    {
        return $this[$name] = (new SelectBox($label, $items))
            ->setHtmlAttribute('size', $size > 1 ? $size : null);
    }

    /**
     * @param $name
     * @param null $label
     * @param null $items
     * @param null $size
     * @return \Nette\Forms\Controls\SelectBox|null
     * @throws \Exception
     */
    public function addSelectAcl($name, $label = NULL, $items = NULL, $size = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = $this->addSelect($name, $label, $items, $size);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * Adds select box control that allows multiple item selection.
     * @param  string|object  $label
     */
    public function addMultiSelect(
        string $name,
               $label = null,
        array $items = null,
        int $size = null
    ): MultiSelectBox {
        return $this[$name] = (new MultiSelectBox($label, $items))
            ->setHtmlAttribute('size', $size > 1 ? $size : null);
    }

    /**
     * @param $name
     * @param null $label
     * @param null $items
     * @param null $size
     * @return \Nette\Forms\Controls\MultiSelectBox|null
     * @throws \Exception
     */
    public function addMultiSelectAcl($name, $label = NULL, $items = NULL, $size = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = $this->addMultiSelect($name, $label, $items, $size);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $caption
     * @return \Nette\Forms\Controls\Checkbox|null
     * @throws \Exception
     */
    public function addCheckboxAcl($name, $caption = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $caption);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addCheckbox($name, $caption);
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @param array|NULL $items
     * @return \Nette\Forms\Controls\CheckboxList|null
     * @throws \Exception
     */
    public function addCheckboxListAcl($name, $label = NULL, array $items = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addCheckboxList($name, $label, $items);
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @return \Nette\Forms\Controls\TextInput|null
     * @throws \Exception
     */
    public function addEmailAcl($name, $label = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addEmail($name, $label);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $default
     * @return \Nette\Forms\Controls\HiddenField|null
     * @throws \Exception
     */
    public function addHiddenAcl($name, $default = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $default);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addHidden($name, $default);
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $src
     * @param null $alt
     * @return \Nette\Forms\Controls\ImageButton|null
     * @throws \Exception
     */
    public function addImageAcl($name, $src = NULL, $alt = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $alt);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addImageButton($name, $src, $alt);
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @return \Nette\Forms\Controls\TextInput|null
     * @throws \Exception
     */
    public function addIntegerAcl($name, $label = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addInteger($name, $label);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @return \Nette\Forms\Controls\TextInput|null
     * @throws \Exception
     */
    public function addNumberAcl($name, $label = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addText($name, $label);
            $item->setHtmlAttribute('class', 'form-control');
            $item->setHtmlType('number');
            $item->setHtmlAttribute('step', '0.01');
            $item->addRule(UI\Form::FLOAT, 'Zadejte platné číslo!');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @param null $cols
     * @param null $maxLength
     * @return \Nette\Forms\Controls\TextInput|null
     * @throws \Exception
     */
    public function addPasswordAcl($name, $label = NULL, $cols = NULL, $maxLength = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addPassword($name, $label, $cols, $maxLength);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @param null $cols
     * @param null $rows
     * @return \Nette\Forms\Controls\TextArea|null
     * @throws \Exception
     */
    public function addTextAreaAcl($name, $label = NULL, $cols = NULL, $rows = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addTextArea($name, $label, $cols, $rows);
            $item->setHtmlAttribute('class', 'form-control');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @param bool $multiple
     * @return \Nette\Forms\Controls\UploadControl|null
     * @throws \Exception
     */
    public function addUploadAcl($name, $label = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            //$item = parent::addUpload($name, $label);
            $item = $this[$name] = new UploadControl($label, false);
            $item->setHtmlAttribute('class', 'form-control-file');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $label
     * @return \Nette\Forms\Controls\TextArea|null
     * @throws \Exception
     */
    public function addEditorAcl($name, $label = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $label);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addTextArea($name, $label);
            $item->setHtmlAttribute('class', 'form-control ckEditor');
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * @param $name
     * @param null $caption
     * @return \Nette\Forms\Controls\SubmitButton|null
     * @throws \Exception
     */
    public function addSubmitAcl($name, $caption = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, 'Tlačítko: ' . $caption);

        if ($action == 'write' || $action == 'read') {
            return parent::addSubmit($name, $caption);
        }
        return NULL;
    }

    /**
     * @param $name
     * @param $title
     * @param null $default
     * @return \Nette\Forms\Controls\HiddenField|null
     * @throws \Exception
     */
    public function addAutocomplete($name, $title, $default = NULL)
    {
        $action = $this->mapper->mapInput($this->user, $this->namePresenter, $this->nameForm, $name, $default);

        if ($action == 'write' || $action == 'read') {
            $item = parent::addHidden($name, $default);
            $item->setHtmlAttribute('class', 'autocomplete-input');
            $item->setHtmlAttribute('data-toggle', 'completer');
            $item->setHtmlAttribute('autocomplete', 'true');
            $item->setHtmlAttribute('title', $title);
            if ($action == 'read') {
                $item->omitted = true;
                $item->disabled = true;
            }
            return $item;
        }
        return NULL;
    }

    /**
     * Set messages on success form - succ save and err save
     * @param array $messageOk [text, type]
     * @param array $messageEr [text, type]
     */
    public function setMessages($messageOk, $messageEr)
    {
        $this->messageOk = $messageOk;
        $this->messageEr = $messageEr;
    }

    /**
     * Set messages on success form - succ save and err save
     * @param string $target redirect target
     */
    public function setRedirect($target, $targetPar = NULL)
    {
        $this->target = $target;
        $this->targetPar = $targetPar;
    }

    /**
     * Set value for autocomplete field
     * @param string $name
     * @param string $value
     */
    public function setAutocmp($name, $value)
    {
        if ($value) {
            $this->components[$name]->setHtmlAttribute('value-autocmp', $value);
        }
    }

    /**
     * Set attribute name -> value to html element
     * @param string $name
     * @param string $nameAttr
     * @param string $valueAttr
     */
    public function setAttr($name, $nameAttr, $valueAttr)
    {
        $this->components[$name]->setHtmlAttribute($nameAttr, $valueAttr);
    }

}