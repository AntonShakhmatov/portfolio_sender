<?php

namespace App\Model\Services;

final class ApiTalksStoreService
{
    public function __construct(
        private string $apiKey // injected from common.neon
        ) {}

    public function getVolnaPracovniMista(): array
    {
        $url = 'https://api.apitalks.store/volna-pracovni-mista';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_HTTPHEADER     => ["x-api-key: {$this->apiKey}", "Accept: application/json"],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 20,
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2,
        ]);
        $resp = curl_exec($ch);
        $err  = curl_error($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($err) {
            throw new \RuntimeException("HTTP error: $err");
        }
        $data = json_decode((string) $resp, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new \RuntimeException("Bad JSON (HTTP $code): $resp");
        }
        return $data;
    }
}