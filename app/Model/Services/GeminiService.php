<?php
declare(strict_types=1);

namespace App\Model\Services;

use Nette\Utils\Json;
use Nette\Utils\JsonException;

final class GeminiService
{
    public function __construct(
        private string $geminiApiKey, // inject z common.neon
    ) {}

    /**
     * Возвращает структурированные данные: ключевые слова, навыки, краткое резюме.
     * При желании можно добавить язык ответа в промпт.
     */
    public function extractKeywords(string $text): array
    {
        $url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key='
             . urlencode($this->geminiApiKey);

        $prompt = <<<PROMPT
        В этом сообщении — резюме. Выдели:
        1) "keywords": список 5–12 ключевых фраз,
        2) "skills": список навыков,
        3) "summary": одно короткое предложение (1–2 строки).

        Верни строго JSON с полями: {"keywords": [...], "skills": [...], "summary": "..."}.
        Текст резюме:
        {$text}
        PROMPT;

        $payload = [
            'contents' => [[
                'parts' => [['text' => $prompt]],
            ]],
        ];

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => Json::encode($payload),
            CURLOPT_TIMEOUT        => 30,
        ]);

        $raw = curl_exec($ch);
        if ($raw === false) {
            $err = curl_error($ch);
            curl_close($ch);
            throw new \RuntimeException('cURL error: ' . $err);
        }

        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            throw new \RuntimeException('Gemini HTTP ' . $httpCode . ': ' . $raw);
        }

        try {
            $resp = Json::decode($raw, Json::FORCE_ARRAY);
        } catch (JsonException $e) {
            throw new \RuntimeException('Invalid JSON from Gemini: ' . $e->getMessage());
        }

        $modelText = $resp['candidates'][0]['content']['parts'][0]['text'] ?? '';
        if ($modelText === '') {
            // иногда Gemini возвращает safetyAnnotations/т.п.
            throw new \RuntimeException('Empty response from Gemini');
        }

        // Просим строго JSON, но всё же попытаемся извлечь
        $clean = trim($modelText);
        // Если модель вернула Markdown-код, вырежем ```json ... ```
        if (preg_match('~```json\s*(\{.*?\})\s*```~is', $clean, $m)) {
            $clean = $m[1];
        }

        try {
            $data = Json::decode($clean, Json::FORCE_ARRAY);
        } catch (JsonException) {
            // fallback: вернём как summary, без падения
            $data = ['keywords' => [], 'skills' => [], 'summary' => $clean];
        }

        return [
            'keywords' => $data['keywords'] ?? [],
            'skills'   => $data['skills']   ?? [],
            'summary'  => $data['summary']  ?? '',
            // 'raw'    => $modelText,
        ];
    }
}