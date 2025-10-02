<?php declare(strict_types = 1);

namespace App\Model\Database\Entity;

use Doctrine\ORM\Mapping as ORM;
use Doctrine\Common\Collections\ArrayCollection;
use Nette\Utils\DateTime;
use Doctrine\ORM\Events;

/**
 * @ORM\Entity(repositoryClass="App\Model\Database\Repository\PermissionItemRepository")
 */
class PermissionItem extends AbstractEntity
{

    const TYPE_ELEMENT = 'element';
    const TYPE_METHOD = 'method';
    const TYPE_PRESENTER = 'presenter';
    const TYPE_FORM_ELEMENT = 'form-element';
    const TYPE_ACTION = 'action';
    const TYPE_FORM = 'form';
    const TYPE_MENU = 'menu';
    const TYPE_GLOBAL_ELEMENT = 'global-element';

    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue
     * GRID type='number'
     * GRID title="Id"
     * GRID sortable='true'
     * GRID visible='true'
     * GRID align='left'
     */
    protected $id;

    /**
     * @ORM\Column(type="string", unique=true)
     * GRID type='text'
     * GRID title="Adresa sekce"
     * GRID sortable='true'
     * GRID filter='single'
     * GRID visible='false'
     */
    protected $name;

    /**
     * @ORM\Column(type="string", nullable=true)
     * GRID type='text'
     * GRID title="Popis sekce"
     * GRID sortable='true'
     * GRID filter='single'
     * GRID visible='true'
     */
    protected $caption;

    /**
     * @ORM\Column(type="string", length=50)
     */
    protected $type;

    public function __construct($data = null)
    {
        parent::__construct($data);
    }

}