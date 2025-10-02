<?php
namespace App\Model\Services;

final class JsonValidator
{
   /** @param array<string, mixed> $data */
    public function validateResume(array $data): array
    {
        $out = [
            'first_name' => $this->strOrNull($data['first_name'] ?? null),
            'last_name'  => $this->strOrNull($data['last_name']  ?? null),
            'email'      => $this->strOrNull($data['email']      ?? null),
            'phone'      => $this->strOrNull($data['phone']      ?? null),
            'skills'     => array_values(array_filter(array_map('strval', $data['skills'] ?? []))),
        ];

        foreach (['first_name','last_name'] as $req) {
            if (!$out[$req]) {
                throw new \InvalidArgumentException("Missing required field: $req");
            }
        }
        return $out;
    }

    private function strOrNull($v): ?string
    {
        $s = is_string($v) ? trim($v) : null;
        return $s === '' ? null : $s;
    }
}