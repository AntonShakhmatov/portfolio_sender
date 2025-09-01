<?php

namespace App\Model\Services;

use GuzzleHttp\Client;

final class ApiWriter
{
    public function __construct(private Client $http, private string $baseUrl, private string $token)
    {
    }

    /** @param array<string,mixed> $payload */
    public function sendLead(array $payload): void
    {
        $this->http->post(rtrim($this->baseUrl, '/').'/leads', [
            'headers' => ['Authorization' => "Bearer {$this->token}"],
            'json'    => $payload,
            'timeout' => 30,
        ]);
    }
}