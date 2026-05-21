package stacholski.com.br.zerotrust_soc;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/incidents")
public class IncidentController {

    @Autowired
    private IncidentRepository repository;

    @Value("${soc.security.api-key}")
    private String validApiKey;

    @PostMapping("/report")
    public ResponseEntity<Map<String, String>> receiveIncidentReport(
            @RequestHeader(value = "X-SOC-Token", required = false) String providedToken,
            @RequestBody Map<String, Object> payload) {

        if (providedToken == null || !providedToken.equals(validApiKey)) {
            System.out.println("\n[!] TENTATIVA DE INVASÃO BLOQUEADA: Falha Zero-Trust.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        Incident incident = new Incident();
        incident.setSource((String) payload.get("source"));
        incident.setAiReport((String) payload.get("ai_report"));
        repository.save(incident);

        System.out.print("\033[H\033[2J");  
        System.out.flush();
        System.out.println("==================================================");
        System.out.println(" 🚨 ALERTA CRÍTICO REGISTRADO NO SOC CENTRAL 🚨 ");
        System.out.println("==================================================");
        System.out.println("ID no Banco : " + incident.getId());
        System.out.println("Origem      : " + incident.getSource());
        System.out.println("Relatório IA:\n" + incident.getAiReport());
        System.out.println("==================================================");

        // MOTOR SOAR: Resposta Automatizada
        Map<String, String> responseBody = new HashMap<>();
        String upperReport = incident.getAiReport().toUpperCase();
        
        if (upperReport.contains("CRÍTICO") || upperReport.contains("CRITICAL")) {
            System.out.println("[⚡] DECISÃO SOAR: Risco alto detectado. Emitindo ordem de SHUTDOWN.");
            responseBody.put("action", "SHUTDOWN");
            responseBody.put("target", incident.getSource());
        } else {
            responseBody.put("action", "LOG_ONLY");
        }

        return ResponseEntity.ok(responseBody);
    }
}