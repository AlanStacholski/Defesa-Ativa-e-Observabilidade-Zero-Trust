package stacholski.com.br.zerotrust_soc;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/incidents")
public class IncidentController {

    @PostMapping("/report")
    public ResponseEntity<String> receiveIncidentReport(@RequestBody Map<String, Object> payload) {
        System.out.println("\n[!] ALERTA RECEBIDO NO SOC CENTRAL [!]");
        System.out.println("Origem: " + payload.get("source"));
        System.out.println("Relatório da IA:\n" + payload.get("ai_report"));
        System.out.println("==================================================\n");

        // Futuramente, é aqui que gravaremos no banco de dados e validaremos tokens Zero-Trust
        
        return ResponseEntity.ok("Incidente registrado com sucesso no SOC.");
    }
}