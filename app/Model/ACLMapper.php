<?php

namespace App\Model;

use App\Model\Database\EntityManager;
use Nette\Application\UI\Presenter;
use Nette\Caching\Cache;
use Nette\Caching\Storage;
use App\Model\Database\Utils\AnnotationParser;
use App\Model\Database\Entity\PermissionItem;
use App\Model\Database\Entity\PermissionRule;
use Nette\Security\User;
use Nette\SmartObject;

class ACLMapper
{
    use SmartObject;

    /** Prefix for anotation */
    const PREFIX = 'ACL';

    /** Admin Group id - for allow all permision */
    const ADMIN_ID = 1;

    /** Default message for denit access */
    const DEFAULT_MESSAGE = 'K této akci nemáte přístup';

    /** @var EntityManager */
    private $em;

    /** @var Storage */
    private $storage;

    /** @var Cache */
    private $cache;

    /** @var AnnotationParser */
    private $parser;

    /** $var Array */
    private $aclList;

    public function __construct(EntityManager $em, Storage $storage, AnnotationParser $ap) {
        $this->em = $em;
        $this->storage = $storage;
        $this->cache = new Cache($this->storage);
        $this->parser = $ap;
        $this->recreateAclList();
    }

    /**
     * Recreate ACL list
     */
    private function recreateAclList($total = false) {
        if ($total) { // clearn cash
            $this->cache->save('ACLPermisionList', null, []);
        }

        $list = $this->cache->load('ACLPermisionList');
        if ($list == NULL) { // if null, create and cash
            $tmp = $this->em->getRepository(PermissionItem::class)->findAll();
            $list = [];
            foreach ($tmp as $item) {
                $list[ $item->name ] = $item;
            }
            $this->cache->save('ACLPermisionList', $list, []);
        }
        $this->aclList = $list;
    }

    /**
     * Mapping function - map and secure access to function
     * @param Presenter $presenter
     * @param User $user
     * @param string $class
     * @param string $function
     * @param PermissionItem $type type of function PRESENTER|METHOD|FORM|ACTION
     */
    public function mapFunction($presenter, $user, $class, $function, $type = PermissionItem::TYPE_METHOD) {
        if ($type == PermissionItem::TYPE_PRESENTER)
            $name = $class;
        else
            $name = $class . "__" . $function;
        $name = str_replace('\\', '_', $name);
        $name = str_replace('App_IntraModule_Presenters_', '', $name);

        $annotation = $this->parser->getMethodPropertyAnnotations($class, $function, self::PREFIX);
        $annotationInfo = [];
        foreach ($annotation as $item) {
            $item = $this->parser->cleanAnnotation($item);
            $annotationInfo[ $item[ 0 ] ] = $item[ 1 ];
        }

        // Check if exist function in ACL list. If not, add function and recreate list
        if (!isset($this->aclList[ $name ])) {
            $item = $this->em->getRepository(PermissionItem::class)->findOneBy(['name' => $name]);
            if (!$item) {
                $item = new PermissionItem();
                $item->setName($name);
                if (!isset($annotationInfo[ 'name' ])) {
                    throw new \Exception('Missing ACL annotation "name", method: ' . $function . ', class: ' . $class);
                }
                $item->setCaption($annotationInfo[ 'name' ]);
                $item->setType($type);

                try {
                    $this->em->persist($item);
                    $this->em->flush();
                } catch (\Doctrine\DBAL\Exception\UniqueConstraintViolationException $e) {
                    \Tracy\Debugger::log(new \Exception('Error in mapping. Mapper try save existing Permision Item - function: mapFunction. Name: ' . $annotationInfo[ 'name' ] . ', method: ' . $function . ', class: ' . $class));
                    return;
                }
            }
            $this->recreateAclList(true);
        }

        /** For admin allow all */
        if ($user->isLoggedIn() && $user->identity->getData()['group'] === self::ADMIN_ID)
            return;

        /* If presenter not set - only mapping */
        if (!isset($presenter))
            return;

        $presenterName = str_replace('\\', '_', get_class($presenter));
        $presenterName = str_replace('App_IntraModule_Presenters_', '', $presenterName);
        // If user have role for presenter - return it
        if (isset($user->identity->roles[ $presenterName ])) {
            if ($user->identity->roles[ $presenterName ] == PermissionRule::ACTION_ALL)
                return;
            if ($user->identity->roles[ $presenterName ] == PermissionRule::ACTION_READ)
                return;
        }

        /* Check if user have anything role - manage acces on page */
        if (!isset($user->identity->roles[ $name ])) {
            if (isset($annotationInfo[ 'rejection' ])) {
                $presenter->flashMessage($annotationInfo[ 'rejection' ], 'warning');
            } else {
                $presenter->flashMessage(self::DEFAULT_MESSAGE, 'warning');
            }
            if (isset($annotationInfo[ 'back-url' ])) {
                $presenter->redirect($annotationInfo[ 'back-url' ]);
            } else {
                $presenter->redirect("Homepage:empty");
            }
        }
    }

    /**
     * Mapping input of form - map and secur access to input.
     * @param User $user
     * @param string $name
     * @param string $label
     * @return string - type of access
     */
    public function mapInput($user, $presenter, $nameForm, $nameElement, $label) {
        $name = $presenter . '__' . $nameForm . '__' . $nameElement;

        $name = str_replace('\\', '_', $name);
        $name = str_replace('App_IntraModule_Presenters_', '', $name);
        // Check if input is in ACL list
        if (!isset($this->aclList[ $name ])) {
            $item = new PermissionItem();
            $item->setName($name);
            if (!isset($label)) {
                $label = $name;
            }
            $item->setCaption($label);
            $item->setType(PermissionItem::TYPE_FORM_ELEMENT);

            try {
                $this->em->persist($item);
                $this->em->flush();
            } catch (\Doctrine\DBAL\Exception\UniqueConstraintViolationException $e) {
                \Tracy\Debugger::log(new \Exception('Error in mapping. Mapper try save existing Permision Item - function: maxInput. Name: ' . $nameElement . ', method: ' . $name));
            }
            $this->recreateAclList(true);
        }

        // For admin allow all to write
        if ($user->isLoggedIn() && $user->identity->getData()['group'] === self::ADMIN_ID)
            return PermissionRule::ACTION_WRITE;

        $presenter = str_replace('App\\IntraModule\\Presenters\\', '', $presenter);

        if (strpos($presenter, 'Modals') !== false) {
            return PermissionRule::ACTION_WRITE;
        }

        // If user have role for presenter
        if (isset($user->identity->roles[ $presenter ])) {
            if ($user->identity->roles[ $presenter ] == PermissionRule::ACTION_ALL)
                return PermissionRule::ACTION_WRITE;
            if ($user->identity->roles[ $presenter ] == PermissionRule::ACTION_READ)
                return PermissionRule::ACTION_READ;
        }

        // If user have role for form
        $fullNameForm = $presenter . '__' . $nameForm;
        if (isset($user->identity->roles[ $fullNameForm ])) {
            if ($user->identity->roles[ $fullNameForm ] == PermissionRule::ACTION_ALL)
                return PermissionRule::ACTION_WRITE;
            if ($user->identity->roles[ $fullNameForm ] == PermissionRule::ACTION_READ)
                return PermissionRule::ACTION_READ;
        }

        return $user->identity->roles[ $name ] ?? NULL;
    }

    /**
     * Mapping html element - map and security who can show and use element
     * @param User $user
     * @param string $presenter
     * @param string $nameElement
     * @param string $caption
     * @return string
     */
    public function mapHtmlControl($user, $presenter, $nameElement, $caption, $type)
    {
        if ($type == PermissionItem::TYPE_FORM) {
            //@TODO cash zpracovaných anotací.
            $annotation = $this->parser->getMethodPropertyAnnotations($presenter, $nameElement, self::PREFIX);
            $annotationInfo = [];
            foreach ($annotation as $item) {
                $item = $this->parser->cleanAnnotation($item);
                $annotationInfo[ $item[ 0 ] ] = $item[ 1 ];
            }
            if (!isset($annotationInfo[ 'name' ])) {
                throw new \Exception('Missing ACL annotation "name", method: ' . $nameElement . ', class: ' . $presenter);
            }
            $caption = $annotationInfo[ 'name' ];
        }
        $presenter = str_replace('App_IntraModule_Presenters_', '', $presenter);
        $presenter = str_replace('App\\IntraModule\\Presenters\\', '', $presenter);
        $name = $presenter . '__' . $nameElement;
        $name = str_replace('\\', '_', $name);

        // Check if input is in ACL list
        if (!isset($this->aclList[ $name ])) {
            $item = new PermissionItem();
            $item->setName($name);
            $item->setCaption($caption);
            if (!$type)
                $type = PermissionItem::TYPE_ELEMENT;
            $item->setType($type);

            try {
                $this->em->persist($item);
                $this->em->flush();
            } catch (\Doctrine\DBAL\Exception\UniqueConstraintViolationException $e) {
                \Tracy\Debugger::log(new \Exception('Error in mapping. Mapper try save existing Permision Item - function: maxInput. Name: ' . $nameElement . ', method: ' . $name));
            }
            $this->recreateAclList(true);
        }
        /** For admin allow all to write */
        if ($user->isLoggedIn() && $user->identity->getData()['group'] === self::ADMIN_ID)
            return PermissionRule::ACTION_SHOW;


        // If user have role for presenter
        if (isset($user->identity->roles[ $presenter ])) {
            if ($user->identity->roles[ $presenter ] == PermissionRule::ACTION_ALL)
                return PermissionRule::ACTION_SHOW;
            if ($user->identity->roles[ $presenter ] == PermissionRule::ACTION_READ)
                return PermissionRule::ACTION_SHOW;
        }
        return $user->identity->roles[ $name ] ?? 'NULL';
    }

    public function getEm()
    {
        return $this->em;
    }
}
