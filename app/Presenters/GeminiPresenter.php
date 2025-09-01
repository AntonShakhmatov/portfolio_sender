<?php
declare(strict_types=1);

namespace App\Presenters;

use Nette;
use Nette\Application\UI\Presenter;
use Nette\Http\IResponse;
use App\Model\Services\GeminiService;

final class GeminiPresenter extends Presenter
{
    /** @var GeminiService @inject */
    public GeminiService $geminiService;

    /**
     * Экшен принимает текст через аргумент маршрута/forward.
     * Если текст большой — лучше передавать ключ, а сам текст хранить в сессии.
     */
    public function actionKeywords(string $prompt = ''): void
    {
        if ($prompt === '') {
            // можно ещё взять из сессии, если передаёшь ключ
            $this->error('Missing prompt', IResponse::S400_BAD_REQUEST);
        }

        // Получаем структурированный ответ от сервиса
        $result = $this->geminiService->extractKeywords($prompt);

        $this->sendJson([
            'ok'       => true,
            'keywords' => $result['keywords'],
            'skills'   => $result['skills'],
            'summary'  => $result['summary'],
            // 'raw'   => $result['raw'], // опционально
        ]);
        // return не нужен, sendJson завершит запрос
        if ($prompt === 'SESSION') {
            $text = $this->getSession('gemini')->text ?? '';
            if ($text === '') $this->error('Empty session text');
            $prompt = $text;
        }
    }
}