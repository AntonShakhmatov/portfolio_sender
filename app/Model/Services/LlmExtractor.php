<?php

namespace App\Model\Services;

use GuzzleHttp\Client;

final class LllmExtractor
{
    public function __construct(private Client $http, private string $apiUrl, private string $apiKey)
    {}

    /** @return array<string,mixed> JSON as array */
    public function extract(array $schema, string $text)
    {
        $schemaJson = json_encode($schema, JSON_UNESCAPED_UNICODE);

        $prompt = <<<PROMPT
Ты извлекаешь поля из текста PDF. Верни строго JSON по СХЕМЕ:

СХЕМА:
$schemaJson

Правила:
- Никакого текста вне JSON.
- Если поле не найдено — null или [] по типу.
Текст:
<<<
$text
>>>
PROMPT;

        $resp = $this->http->post($this->apiUrl, [
            'headers' => [
                'Authorization' => "Bearer {$this->apiKey}",
                'Content-Type'  => 'application/json',
            ],
            'json' => [
                'model' => 'auto',
                'messages' => [['role'=>'user','content'=>$prompt]],
                'response_format' => ['type'=>'json_object'],
            ],
            'timeout' => 60,
        ]);

        
        $data = json_decode((string)$resp->getBody(), true);
        $raw = $this->extractTextFromResponse($data);

        $out = json_decode($raw, true);
        if (!is_array($out)) {
            throw new \RuntimeException('LLM did not return valid JSON.');
        }
        return $out;
    }

    private function extractTextFromResponse(array $data): string
    {
        return $data['choices'][0]['message']['content'] ?? '{}';
    }
}