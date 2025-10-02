<?php 

declare(strict_types=1);

namespace App\Presenters;

use Nette;
use Nette\Application\UI\Form;
use Nette\Utils\ArrayHash;
use Nette\Http\IResponse;
use Nette\Database\Explorer;
use Nette\Utils\Json;
use App\Model\Services\GeminiService;
use App\Model\Services\EmbeddingsService;
use App\Model\ACLForm;
use App\Forms\UploadFormFactory;
use App\Model\Services\PdfTextExtractor;
use Smalot\PdfParser\Parser as Smalot;
use Symfony\Component\Process\Process;
use Nette\Application\Responses\TextResponse;

final class HomepagePresenter extends Nette\Application\UI\Presenter
{

    protected function startup(): void
    {
        parent::startup();
        $session = $this->getSession();
        if (!$session->isStarted()) {
            $session->start();
        }
    }

    public function __construct(
        private UploadFormFactory $uploadFormFactory, 
        private PdfTextExtractor $extractor,
        private GeminiService $gemini,
        private Explorer $database,
        private bool $preferPdfToText = true,
        )
    {
        parent::__construct();
        $this->database = $database;
    }

    /** @var EmbeddingsService @inject */
    public $embeddingsService;

    public function createComponentChatWindowModalForm()
    {
        $form = new ACLForm();
        $form->addRadioList(
            'predefined',
            '',
            [
                'works' => 'Hledám si info o aktualnich nabidkach',
                'markets' => 'Hledám dostupny bůrže',
                'workers' => 'Hledám pracovnika',
            ]
        )->setHtmlAttribute('class', 'form-check-input mb-2')
            ->setOption('rendered', true);
    
        $form->addText('text', '')
            ->setHtmlAttribute('placeholder', 'Zadejte dotaz')
            ->setHtmlAttribute('class', 'form-control input-md messageInput');
    
        $form->addSubmit('send', '')
                ->setHtmlAttribute('class', 'sendButton ajax');
    
        $form->isRedirect = false;
        $form->onSuccess[] = [$this, 'chatFormSucceeded'];
    
        return $form;
    }        

    /** @var Nette\Database\Context @inject */
        public $db;

    public function chatFormSucceeded(Form $form, \stdClass $values): void
    {
        $text = $values->text;

        $user_embedding = $this->embeddingsService->get_embedding([$text])[0];

        $products = $this->db->query("SELECT * FROM embedding")->fetchAll();

        $articles = $this->db->query("SELECT * FROM embedding_article")->fetchAll();

        $contacts = $this->db->query("SELECT * FROM embedding_article")->fetchAll();

        $works = $this->db->query("SELECT * FROM embedding_article")->fetchAll();

        $scores = [];
        foreach ($products as $p) {
            $embedding = json_decode($p['union_date'], true);
            if (!$embedding || !is_array($embedding)) {
                continue;
            }
            $score = $this->embeddingsService->cosine_similarity($user_embedding, $embedding);
            // $score = $this->embeddingsService->findMostSimilarProducts($embedding);
            $scores[] = ['score' => $score, 'id' => $p['id'], 'union_date' => $p['union_date']];
        }

        foreach ($articles as $article) {
            $embedding = json_decode($article['union_date'], true);
            if (!$embedding || !is_array($embedding)) {
                continue;
            }
            $score = $this->embeddingsService->cosine_similarity($user_embedding, $embedding);
            // $score = $this->embeddingsService->findMostSimilarProducts($embedding);
            $scores[] = ['score' => $score, 'id' => $article['id'], 'union_date' => $article['union_date']];
        }

        foreach ($contacts as $c) {
            $embedding = json_decode($c['union_date'], true);
            if (!$embedding || !is_array($embedding)) {
                continue;
            }
            $score = $this->embeddingsService->cosine_similarity($user_embedding, $embedding);
            // $score = $this->embeddingsService->findMostSimilarProducts($embedding);
            $scores[] = ['score' => $score, 'id' => $c['id'], 'union_date' => $c['union_date']];
        }


        foreach ($works as $w) {
            $embedding = json_decode($w['union_date'], true);
            if (!$embedding || !is_array($embedding)) {
                continue;
            }
            $score = $this->embeddingsService->cosine_similarity($user_embedding, $embedding);
            // $score = $this->embeddingsService->findMostSimilarProducts($embedding);
            $scores[] = ['score' => $score, 'id' => $w['id'], 'union_date' => $w['union_date']];
        }

        usort($scores, fn($a, $b) => $b['score'] <=> $a['score']);

        $top5 = array_slice($scores, 0, 5);
    }

    protected function createComponentUploadForm(): Form
    {
        return $this->uploadFormFactory->create(function (): void {
            $this->flashMessage('Soubor uložen.', 'success');
            $this->redirect('this');
        });
    }

    public function actionCreate(): void
    {
        $result = ['summary' => '', 'keywords' => [], 'skills' => []];
    
        try {
            $text   = $this->extractTextFromLastUpload();
            $ai     = $this->gemini->extractKeywords($text) ?? [];
    
            $result['summary']  = (string) ($ai['summary']  ?? '');
            $result['keywords'] = array_values((array) ($ai['keywords'] ?? []));
            $result['skills']   = array_values((array) ($ai['skills']   ?? []));
    
            $rowId = $this->saveProfileResult($result);
    
            $this->sendJson([
                'ok'       => true,
                'id'       => $rowId,
                'message'  => 'Soubor uložen.',
                'redirect' => $this->link('Homepage:create'),
                'summary'  => $result['summary'],
                'keywords' => $result['keywords'],
                'skills'   => $result['skills'],
            ]);
        } catch (\Throwable $e) {
            $this->sendJson([
                'ok'    => false,
                'error' => $e->getMessage(),
            ]);
        }
    }    

    private function saveProfileResult(array $j): int
    {
        $row = $this->database->table('profile_skills')->insert([
            'summary'  => $j['summary'],
            'keywords' => Json::encode($j['keywords']),
            'skills'   => Json::encode($j['skills']),
        ]);
        return (int) $row->getPrimary();
    }    

    private function extractTextFromLastUpload(): string
    {
        $section  = $this->getSession('upload');
        $filename = $section->lastFile ?? null;
        if (!$filename) {
            $this->error('No file in session.', IResponse::S404_NOT_FOUND);
        }

        $root = dirname(__DIR__, 2); // /var/www/html
        $path = $root . '/www/uploads/' . basename($filename);
        // $path = rtrim($this->wwwDir, '/\\') . '/uploads/' . basename((string)$filename);
        if (!is_file($path)) {
            $this->error("PDF not found: $path", IResponse::S404_NOT_FOUND);
        }

        // 1) pdftotext
        $bin = shell_exec('which pdftotext');
        if ($this->preferPdfToText && $bin !== null && trim($bin) !== '') {
            $cmd = ['pdftotext', '-layout', '-enc', 'UTF-8', $path, '-'];
            $p = new Process($cmd);
            $p->run();
            if ($p->isSuccessful()) {
                $out = $p->getOutput();
                if (mb_strlen(trim($out)) > 0) {
                    return $out;
                }
            }
        }

        // 2) fallback: Smalot
        $parser = new Smalot();
        $pdf    = $parser->parseFile($path);
        return $pdf->getText();
    }

    public function actionRead(): void
    {
        $text = $this->extractTextFromLastUpload();
        $this->getHttpResponse()->setContentType('text/plain', 'UTF-8');
        $this->sendResponse(new TextResponse($text));
    }

    // public function actionDefault(): void
    // {
    //     $path = dirname(__DIR__, 2) . '/.docker/embedding/server/job_parsed.json';

    
    //     if (!is_file($path)) {
    //         throw new \RuntimeException("Файл не найден: $path");
    //     }
    
    //     $json = file_get_contents($path);
    //     if ($json === false) {
    //         throw new \RuntimeException('Не удалось считать job_parsed.json');
    //     }
    
    //     $data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);

    //     $array = json_encode($data);

    //     $row = [
    //         'title'   => $array['title']    ?? '',
    //         'company' => $array['company']  ?? '',
    //         'location'=> $array['location'] ?? '',
    //         'salary'  => $array['salary']   ?? '',
    //         'url'     => $array['url']      ?? '',
    //     ];

    //     print_r($row);
    // }    
}
