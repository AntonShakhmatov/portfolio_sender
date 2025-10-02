<?php
namespace App\Model\Facade;

use App\Components\MailSender\MailSender;
// use App\Model\Database\EntityManager;
use Doctrine\ORM\EntityManagerInterface;
use App\Model\Utils\SMSSluzba;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use App\Presenters\EmbeddingsPresenter;
use App\Bootstrap;
use App\Model\Services\EmbeddingsService;
use App\Model\Services\OffersService;

class Cron
{
    private EntityManagerInterface $em;
    private EmbeddingsService $embeddingsService;
    private OffersService $offersService;

    public function __construct(
        EntityManagerInterface $em,
        EmbeddingsService $embeddingsService,
        OffersService $offersService
    )
    {
        $this->em = $em;
        $this->embeddingsService = $embeddingsService;
        $this->offersService = $offersService;
    }

    private function removeDiacritic($text = ''): string
    {
        $prevodni_tabulka = Array(
            'ä'=>'a',
            'Ä'=>'A',
            'á'=>'a',
            'Á'=>'A',
            'à'=>'a',
            'À'=>'A',
            'ã'=>'a',
            'Ã'=>'A',
            'â'=>'a',
            'Â'=>'A',
            'č'=>'c',
            'Č'=>'C',
            'ć'=>'c',
            'Ć'=>'C',
            'ď'=>'d',
            'Ď'=>'D',
            'ě'=>'e',
            'Ě'=>'E',
            'é'=>'e',
            'É'=>'E',
            'ë'=>'e',
            'Ë'=>'E',
            'è'=>'e',
            'È'=>'E',
            'ê'=>'e',
            'Ê'=>'E',
            'í'=>'i',
            'Í'=>'I',
            'ï'=>'i',
            'Ï'=>'I',
            'ì'=>'i',
            'Ì'=>'I',
            'î'=>'i',
            'Î'=>'I',
            'ľ'=>'l',
            'Ľ'=>'L',
            'ĺ'=>'l',
            'Ĺ'=>'L',
            'ń'=>'n',
            'Ń'=>'N',
            'ň'=>'n',
            'Ň'=>'N',
            'ñ'=>'n',
            'Ñ'=>'N',
            'ó'=>'o',
            'Ó'=>'O',
            'ö'=>'o',
            'Ö'=>'O',
            'ô'=>'o',
            'Ô'=>'O',
            'ò'=>'o',
            'Ò'=>'O',
            'õ'=>'o',
            'Õ'=>'O',
            'ő'=>'o',
            'Ő'=>'O',
            'ř'=>'r',
            'Ř'=>'R',
            'ŕ'=>'r',
            'Ŕ'=>'R',
            'š'=>'s',
            'Š'=>'S',
            'ś'=>'s',
            'Ś'=>'S',
            'ť'=>'t',
            'Ť'=>'T',
            'ú'=>'u',
            'Ú'=>'U',
            'ů'=>'u',
            'Ů'=>'U',
            'ü'=>'u',
            'Ü'=>'U',
            'ù'=>'u',
            'Ù'=>'U',
            'ũ'=>'u',
            'Ũ'=>'U',
            'û'=>'u',
            'Û'=>'U',
            'ý'=>'y',
            'Ý'=>'Y',
            'ž'=>'z',
            'Ž'=>'Z',
            'ź'=>'z',
            'Ź'=>'Z'
        );

        return strtr($text, $prevodni_tabulka);
    }

    public function makeEmbeddingsCommand()
    {
        
        $this->embeddingsService->processProducts();
        $this->embeddingsService->processArticles();
    }

    public function makeOffersCommand()
    {
        $this->offersService->processOffersRewrite();
    }

    public function makeOffersForPraceZaRohemCommand()
    {
        $this->offersService->processOffersPraceZaRohemRewrite();
    }

    public function makeOffersForJobstackit()
    {
        $this->offersService->processOffersJockstackitRewrite();
    }
}