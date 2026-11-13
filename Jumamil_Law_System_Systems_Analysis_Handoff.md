# JUMAMIL LAW SYSTEM

## Systems Analysis and Development Handoff Document

**Project title:** JUMAMIL LAW SYSTEM: Web-Based Legal Document
Archiving and Tracking System with AI Optical Character Recognition
(OCR) Integration for Jumamil Law Office\
**Document version:** 1.0 --- Consolidated working baseline\
**Prepared for:** Capstone Project Development Team\
**Date:** 13 November 2026\
**Status:** Initial Systems Analysis approved; detailed design and
technical validation pending

------------------------------------------------------------------------

## Document Purpose and Instructions for the Development Team

This document consolidates the current project understanding, approved
scope, functional and non-functional requirements, conceptual data
model, assumptions, unresolved questions, and traceability information.
It is intended to serve as the primary handoff context for system design
and implementation, including use with another AI coding assistant.

### Instructions to any AI or developer using this document

1.  Treat this document as the current project baseline. Do not silently
    add features, roles, integrations, or workflows that are not
    described here.
2.  Distinguish **confirmed decisions**, **proposed design decisions**,
    **assumptions**, and **unresolved questions**. Never present an
    unresolved matter as confirmed.
3.  Keep the first release focused on the Minimum Viable Product (MVP).
    Do not expand scope simply because a feature might be useful.
4.  Preserve the law office's physical/legal processes. The system
    supports document preparation, review, tracking, archiving, and
    retrieval; it does not replace wet-ink signing, the physical
    Notarial Register, or the attorney's legal judgment.
5.  Do not implement automatic official-number generation or
    rearrangement unless the Attorney validates the exact office
    procedure and legal requirements.
6.  OCR output is unverified until a human reviews and confirms it.
    Preserve the original scanned file separately from OCR text and
    metadata.
7.  Do not overwrite previous document versions, attorney comments, or
    review decisions.
8.  Before coding, complete the logical database design, use cases,
    role/permission matrix, wireframes, architecture decisions, and
    proof-of-concept testing for the editor and OCR.
9.  When information is missing, record it as an open question and ask
    the project team/client. Do not guess.
10. When proposing code, explain the purpose and trade-offs, keep
    implementation modular, and implement in small testable increments.

------------------------------------------------------------------------

# I. Project Overview

## 1.1 Project Description

The Jumamil Law System is a proposed web-based application for Jumamil
Law Office. It is intended to organize client information, legal service
requests, document templates, document preparation, attorney review,
document revisions and version history, signed-document uploads, OCR
processing, digital archiving, and document retrieval.

Office staff will manage client records and requests, prepare documents
using templates or authorized manual preparation, and submit documents
for attorney review. The Attorney will review documents, provide
correction comments, and approve documents for printing. After printing,
the Attorney will perform the required physical signing. Signed
documents will be scanned using the office's physical scanner and
uploaded to the system. OCR will extract searchable text and attempt to
identify relevant metadata. Authorized users must verify extracted
metadata before the document is considered archived.

The system is intended to improve the organization, tracking, storage,
and retrieval of legal documents while retaining the office's existing
physical procedures and records.

## 1.2 General Objective

To design and develop a web-based legal document archiving and tracking
system with AI-assisted OCR integration for Jumamil Law Office to
improve the management, tracking, storage, and retrieval of legal
documents.

## 1.3 Specific Objectives

1.  Establish a centralized repository for client records, legal service
    requests, document templates, document versions, and signed document
    archives.
2.  Provide a document preparation and attorney review workflow.
3.  Preserve document versions, attorney comments, and review history.
4.  Integrate OCR for searchable text extraction and assisted metadata
    extraction from scanned documents.
5.  Provide search and retrieval by client, document type, date,
    official number, register references where applicable, and
    OCR-extracted text.
6.  Implement internal user authentication, access controls, and
    activity records.
7.  Support digital archiving while retaining physical signed originals
    in the office.

## 1.4 Intended Users and Stakeholders

-   **Office Staff:** Internal users who manage client information and
    requests, prepare documents, upload templates, revise documents,
    print approved documents, upload scans, verify OCR metadata when
    authorized, and retrieve records.
-   **Attorney:** The law office's attorney, responsible for document
    review, correction comments, approval for printing, official
    numbering through the existing office process, physical signing, and
    relevant archive verification.
-   **Clients:** External stakeholders who visit the office and request
    legal services. Clients do not have system accounts.
-   **Project Development Team:** Responsible for requirements
    validation, design, development, testing, deployment, and
    documentation.

There is one Attorney at this specific law office. The system's two
primary role types are Office Staff and Attorney. This does not imply
that a role type can only ever have one account, although the expected
office configuration has one Attorney account.

------------------------------------------------------------------------

# II. Stakeholders and User Roles

## 2.1 Role Responsibilities

### Office Staff

-   Search for and register client profiles.
-   Create and manage legal service requests.
-   Associate multiple documents with a request.
-   Upload, organize, and manage document templates, subject to approved
    permissions.
-   Prepare and edit documents using the embedded editor.
-   Save drafts and submit documents for attorney review.
-   Revise and resubmit documents when corrections are requested.
-   Print documents approved by the Attorney.
-   Upload scanned signed documents from the office computer.
-   Review and verify OCR-extracted information when authorized.
-   Search and retrieve authorized client and archive records.

### Attorney

-   Review documents submitted by staff.
-   Add comments and request corrections.
-   Approve documents for printing.
-   Assign or record official document numbers through the existing
    office process.
-   Physically sign documents using wet ink.
-   Scan signed documents using the office's physical scanner.
-   Upload or oversee upload of scanned documents.
-   Verify OCR-extracted metadata and archive records as required.
-   Search and retrieve authorized records.

## 2.2 Client Access

Clients are stakeholders but are not system users. There will be no
client login, public client portal, or self-service document submission
in the MVP.

## 2.3 Account Administration --- Proposed Design

The current recommendation is to retain only two primary role types:
Office Staff and Attorney. A separate Administrator role is not required
for the initial design. Instead, the Attorney account may receive an
additional user-management permission to create staff accounts,
activate/deactivate accounts, and manage access.

A secure first-run setup should establish the initial Attorney account.
Permanent shared default credentials or hard-coded administrator
credentials must not be used.

**Status:** Proposed design decision; confirm with the project leader
and law office before implementation.

------------------------------------------------------------------------

# III. Scope and Delimitations

## 3.1 In-Scope Features

The planned system scope includes:

1.  Internal authentication and access control for Office Staff and
    Attorney.
2.  Client profile management.
3.  Legal service request management.
4.  Multiple documents associated with one request.
5.  Template upload, organization, search, creation, and management.
6.  Embedded rich-text document preparation and editing.
7.  Attorney review, comments, correction requests, and approval for
    printing.
8.  Document version history.
9.  Printing workflow and recording of official document numbers and
    applicable register references.
10. Recording physical signing status.
11. Scanned PDF upload and association with client, request, and
    document records.
12. OCR text extraction and assisted metadata extraction.
13. Human verification and correction of OCR metadata.
14. Centralized digital archive and document search.
15. Basic activity records and reports.
16. Storage and backup mechanisms.
17. Excel/PDF report exports for manual submission where required.

## 3.2 Out-of-Scope Features and Delimitations

-   Client accounts and public-facing client portal.
-   Native mobile application.
-   Direct government or judicial API integration.
-   Automated external submission to government or judicial systems.
-   Replacing the physical wet-ink signing process.
-   Replacing the physical Notarial Register or other official bound
    records.
-   Automatic legal decision-making or document approval by AI.
-   Automatic generation, rearrangement, or correction of official
    numbers without validated office rules.
-   Automatic deletion of local files after cloud synchronization.
-   Full replacement of Microsoft Word unless editor feasibility and
    required formatting are demonstrated and explicitly approved.
-   Guaranteed automatic splitting of every multi-document PDF.

## 3.3 Operational Boundaries

Face-to-face client interaction, physical printing and handling,
official numbering under the office's existing process, wet-ink signing,
physical storage of originals, and manual external submissions remain
outside direct system control.

## 3.4 Technical Boundaries

The system is planned as a browser-based application with a database,
file storage, OCR processing, authentication/access control, and backup
capabilities. The exact technology stack, hosting model, OCR engine,
editor library, and deployment architecture remain to be selected and
validated.

------------------------------------------------------------------------

# IV. Existing Office Workflow (As-Is)

The currently understood workflow is:

1.  A client physically visits the law office and makes a request.
2.  Office staff receives the request and relevant client information.
3.  Staff uses Windows File Explorer to locate an existing document
    template.
4.  Staff prepares the requested document.
5.  The Attorney reviews the document.
6.  If corrections are needed, the Attorney communicates comments and
    staff revises the document.
7.  Once approved, the document may be printed by an available staff
    member.
8.  The Attorney assigns or records the official number through the
    office's existing process and physically signs the document.
9.  The signed document is scanned using a physical scanner.
10. The scanned output is saved to a computer.
11. The Attorney currently uses OCR to maintain digital copies; the
    exact existing digital filing arrangement has not yet been
    established.
12. For older records, staff may need to search physical logbooks, which
    can be slow.

**Limitations of the current process identified so far:** templates are
stored in File Explorer; document preparation and review involve manual
handling; revisions need reliable history; signed scans need organized
digital association; and historical retrieval through physical logbooks
can be slow.

Do not assume the office already has a centralized digital repository,
automated OCR metadata extraction, cloud synchronization, or automated
document tracking.

------------------------------------------------------------------------

# V. Proposed System Workflow (To-Be)

1.  An internal user logs in.
2.  Staff searches for an existing client profile.
3.  If no matching profile exists, staff registers a new client.
4.  Staff creates a legal service request for the client.
5.  Staff associates one or more documents with the request.
6.  Staff selects an existing template or uses an authorized manual
    preparation process.
7.  Staff prepares or revises the document in the embedded rich-text
    editor.
8.  Staff saves the draft and submits it for Attorney review.
9.  The Attorney reviews the submitted version.
10. If corrections are required, the Attorney records comments.
11. Staff revises the existing document record; the system preserves the
    prior version and creates a new version.
12. Staff resubmits the revised version.
13. The Attorney approves the appropriate version for printing.
14. An authorized staff member prints the approved document.
15. The Attorney assigns or records the official number through the
    existing office process and performs the required wet-ink signing.
16. The physical signed original remains stored by the office.
17. The signed document is scanned using the physical scanner and saved
    to a computer.
18. An authorized user uploads the scanned PDF to the system and
    associates it with the appropriate document record.
19. The system supports individual scanned documents and PDFs that may
    contain multiple documents. Boundary detection and splitting may be
    attempted where feasible, with human review.
20. OCR extracts searchable text and attempts to identify metadata.
21. An authorized user reviews and corrects extracted metadata.
22. The system stores the original scanned PDF, OCR text, and verified
    metadata.
23. Authorized users search and retrieve records by client name,
    document type, date, official number, applicable register
    references, and OCR full text.
24. A request is considered completed when every associated document has
    received its required physical Attorney signature, even if digital
    archiving is still pending.

## 5.1 Proposed Document Statuses

-   Draft
-   Submitted for Review
-   Under Review
-   Revision Required
-   Resubmitted
-   Approved for Printing
-   Awaiting Wet-Ink Signature
-   Signed / Executed
-   Scanned and Archived

**Status distinction:** - **Signed / Executed:** The Attorney has
physically signed the document using wet ink. - **Scanned and
Archived:** The signed document has been uploaded, OCR processing has
been performed, and the required metadata has been verified.

Approval for printing is not the same as final physical execution. A
document can be signed while still awaiting digital archiving.

------------------------------------------------------------------------

# VI. Business Rules

The following rules represent the current business-rule baseline. Any
legal or office-specific numbering rule must be validated by the
Attorney.

## 6.1 Client and Request Rules

-   **BR-CL-001:** Each client shall have a distinct client record.
-   **BR-CL-002:** A client may have multiple legal service requests.
-   **BR-REQ-001:** Each request shall be associated with one client.
-   **BR-REQ-002:** A request may contain multiple documents.
-   **BR-REQ-003:** Each request document shall belong to one request.

## 6.2 Template and Document Rules

-   **BR-TEMP-001:** A generated document may be prepared using an
    available template or an authorized manual preparation process.
-   **BR-TEMP-002:** Templates shall be stored separately from generated
    legal documents.
-   **BR-DOC-001:** Each generated document shall be associated with its
    relevant client through its request.
-   **BR-DOC-002:** A document shall be submitted for Attorney review
    before it can be approved for printing.

## 6.3 Review and Version Rules

-   **BR-REV-001:** Only the Attorney may approve a document for
    printing.
-   **BR-REV-002:** When corrections are required, the Attorney shall
    provide comments describing the requested changes.
-   **BR-VER-001:** Staff shall revise the existing document record and
    submit a new version rather than overwrite the previous version.
-   **BR-VER-002:** Previous document versions, Attorney comments, and
    review decisions shall be preserved.
-   **BR-REV-003:** A document shall not be treated as approved for
    printing until the Attorney records approval.

No permanent rejection workflow, automatic rejection condition, revision
limit, or review deadline is established at this time.

## 6.4 Printing, Numbering, and Signing Rules

-   **BR-SIG-001:** Only documents approved by the Attorney may proceed
    to printing.
-   **BR-SIG-002:** Any authorized staff member may print an approved
    document.
-   **BR-SIG-003:** Official numbers shall be assigned or recorded
    through the office's existing process.
-   **BR-SIG-004:** The system shall record official numbers and
    applicable register references without independently rearranging
    official numbering.
-   **BR-SIG-005:** Required physical signing shall be performed by the
    Attorney.
-   **BR-SIG-006:** Approval for printing shall not be treated as proof
    of physical signing.

## 6.5 Archiving and OCR Rules

-   **BR-ARC-001:** A signed document shall be uploaded before it can be
    digitally archived.
-   **BR-ARC-002:** OCR processing shall be performed on supported
    uploaded scans.
-   **BR-ARC-003:** OCR-extracted metadata shall be reviewed and
    verified by an authorized human user.
-   **BR-ARC-004:** The original scanned file and OCR-extracted
    information shall be preserved separately.
-   **BR-ARC-005:** A document shall be considered digitally archived
    only after upload, OCR processing, and required metadata
    verification are complete.
-   **BR-ARC-006:** The physical signed original shall remain stored by
    the office.

## 6.6 Search Rules

-   **BR-SRCH-001:** Authorized users may search archived records using
    available metadata and OCR-extracted text.
-   **BR-SRCH-002:** Archived records shall retain their association
    with the relevant client, request, and document.

## 6.7 Request Completion Rules

-   **BR-REQ-004:** A request shall remain in progress until every
    associated document has received its required physical Attorney
    signature.
-   **BR-REQ-005:** A request may be marked completed once all
    associated documents have been physically signed, even if one or
    more signed documents are still awaiting digital archiving.

## 6.8 User and Access Rules

-   **BR-USER-001:** Only authenticated internal users may access
    protected system functions.
-   **BR-USER-002:** Access shall be restricted according to assigned
    roles and permissions.
-   **BR-USER-003:** Attorney-specific review and approval actions shall
    be restricted to the Attorney role.
-   **BR-USER-004:** Important user activities shall be recorded.

## 6.9 Storage Rules

-   **BR-STOR-001:** Documents shall be stored in an organized central
    repository.
-   **BR-STOR-002:** The system shall support backup of important
    records and files.
-   **BR-STOR-003:** Successful synchronization shall not automatically
    authorize deletion of local copies.
-   **BR-STOR-004:** Local file offloading or deletion shall be
    restricted to authorized personnel.

------------------------------------------------------------------------

# VII. Functional Requirements

Priority labels: - **Must:** Required for the MVP. - **Should:**
Important, but may be scheduled after the essential workflow if time or
technical constraints require it.

## 7.1 Authentication and User Access

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-AUTH-001             The system shall        Must
                          require internal users  
                          to log in using valid   
                          credentials.            

  FR-AUTH-002             The system shall        Must
                          distinguish between     
                          Office Staff and        
                          Attorney roles.         

  FR-AUTH-003             The system shall        Must
                          restrict functions      
                          according to the user's 
                          assigned role and       
                          permissions.            

  FR-AUTH-004             The system shall allow  Must
                          users to log out        
                          securely.               

  FR-AUTH-005             The system shall        Must
                          prevent unauthorized    
                          users from accessing    
                          protected pages and     
                          records.                

  FR-AUTH-006             The system shall allow  Must
                          authorized account      
                          administrators to       
                          manage user accounts.   
  -----------------------------------------------------------------------

**Account administration proposal:** The Attorney may receive
user-management permission to create staff accounts, activate/deactivate
accounts, and manage access. A secure first-run setup should establish
the initial Attorney account. This remains pending validation.

## 7.2 Client Management

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-CL-001               The system shall allow  Must
                          authorized staff to     
                          register new client     
                          records.                

  FR-CL-002               The system shall store  Must
                          relevant client         
                          information, including  
                          name and contact        
                          details.                

  FR-CL-003               The system shall allow  Must
                          authorized users to     
                          view and update client  
                          information.            

  FR-CL-004               The system shall allow  Must
                          users to search for     
                          existing clients.       

  FR-CL-005               The system shall        Must
                          display a client's      
                          associated requests and 
                          documents.              
  -----------------------------------------------------------------------

The interface should encourage users to search for an existing client
before creating a new record to reduce duplicate profiles.

## 7.3 Legal Service Request Management

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-REQ-001              The system shall allow  Must
                          authorized staff to     
                          create a legal service  
                          request for a client.   

  FR-REQ-002              The system shall        Must
                          associate each request  
                          with an existing client 
                          record.                 

  FR-REQ-003              The system shall allow  Must
                          multiple documents to   
                          be associated with one  
                          request.                

  FR-REQ-004              The system shall record Must
                          the request date and    
                          relevant request        
                          information.            

  FR-REQ-005              The system shall        Must
                          display the documents   
                          and their respective    
                          statuses under a        
                          request.                

  FR-REQ-006              The system shall track  Must
                          whether a request is in 
                          progress or completed.  
  -----------------------------------------------------------------------

A request is completed based on required physical signatures, not
necessarily completion of digital archiving.

## 7.4 Template Management

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-TEMP-001             The system shall allow  Must
                          authorized staff to     
                          upload existing         
                          document templates from 
                          their computers.        

  FR-TEMP-002             The system shall store  Must
                          templates separately    
                          from generated legal    
                          documents.              

  FR-TEMP-003             The system shall allow  Must
                          templates to be         
                          organized by category   
                          or document type.       

  FR-TEMP-004             The system shall allow  Must
                          authorized users to     
                          search and select       
                          available templates.    

  FR-TEMP-005             The system shall allow  Must
                          authorized staff to     
                          create and save new     
                          templates.              

  FR-TEMP-006             The system shall allow  Should
                          authorized users to     
                          update or manage        
                          existing templates.     
  -----------------------------------------------------------------------

Existing templates stored in Windows File Explorer are candidates for
migration. Actual file formats and compatibility must be evaluated using
sample office templates.

## 7.5 Document Preparation and Editing

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-DOC-001              The system shall allow  Must
                          authorized staff to     
                          create a document under 
                          a legal service         
                          request.                

  FR-DOC-002              The system shall allow  Must
                          staff to prepare        
                          documents using         
                          available templates.    

  FR-DOC-003              The system shall        Must
                          provide an embedded     
                          rich-text editor for    
                          preparing and editing   
                          documents.              

  FR-DOC-004              The editor shall        Must
                          support basic           
                          formatting, including   
                          bold, italic,           
                          underline, font         
                          settings, paragraph     
                          alignment, lists, and   
                          tables.                 

  FR-DOC-005              The system shall allow  Must
                          staff to save documents 
                          as drafts.              

  FR-DOC-006              The system shall        Must
                          associate each          
                          generated document with 
                          its client and request. 

  FR-DOC-007              The system shall allow  Must
                          staff to revise         
                          documents that require  
                          corrections.            

  FR-DOC-008              The system shall        Must
                          provide an appropriate  
                          output format for       
                          printing approved       
                          documents.              
  -----------------------------------------------------------------------

**Technical caveat:** An embedded rich-text editor is not automatically
a full Microsoft Word replacement. Advanced pagination, page breaks,
headers/footers, page numbering, and DOCX fidelity must be tested with
actual office templates before selecting the editor and import/export
approach.

## 7.6 Attorney Review and Approval

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-REV-001              The system shall allow  Must
                          staff to submit         
                          prepared documents for  
                          Attorney review.        

  FR-REV-002              The system shall make   Must
                          submitted documents     
                          visible to the Attorney 
                          for review.             

  FR-REV-003              The Attorney shall be   Must
                          able to review          
                          submitted documents.    

  FR-REV-004              The Attorney shall be   Must
                          able to provide         
                          comments explaining     
                          required corrections.   

  FR-REV-005              The system shall mark   Must
                          documents requiring     
                          corrections for staff   
                          revision.               

  FR-REV-006              The system shall allow  Must
                          staff to revise and     
                          resubmit documents.     

  FR-REV-007              The Attorney shall be   Must
                          the authorized user who 
                          approves documents for  
                          printing.               

  FR-REV-008              The system shall record Must
                          review decisions and    
                          their corresponding     
                          dates.                  
  -----------------------------------------------------------------------

The initial workflow supports correction and resubmission. A permanent
rejection process is not included unless confirmed by the office.

## 7.7 Document Version Management

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-VER-001              The system shall create Must
                          a new version when      
                          staff revise a document 
                          after receiving         
                          corrections.            

  FR-VER-002              The system shall        Must
                          preserve previous       
                          document versions.      

  FR-VER-003              The system shall        Must
                          maintain comments and   
                          review decisions        
                          associated with         
                          document versions.      

  FR-VER-004              The system shall        Must
                          display the version     
                          history of a document.  

  FR-VER-005              The system shall        Must
                          identify the latest     
                          version of a document.  
  -----------------------------------------------------------------------

## 7.8 Printing, Official Numbering, and Physical Signing

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-SIG-001              The system shall allow  Must
                          authorized staff to     
                          print documents         
                          approved by the         
                          Attorney.               

  FR-SIG-002              The system shall        Must
                          prevent documents from  
                          being marked as         
                          approved for printing   
                          without Attorney        
                          approval.               

  FR-SIG-003              The system shall allow  Must
                          authorized users to     
                          record the official     
                          document number         
                          assigned through the    
                          office's existing       
                          process.                

  FR-SIG-004              The system shall allow  Should
                          authorized users to     
                          record relevant         
                          notarial register       
                          references when         
                          applicable.             

  FR-SIG-005              The system shall record Must
                          whether a document has  
                          received the Attorney's 
                          required physical       
                          signature.              

  FR-SIG-006              The system shall        Must
                          distinguish approval    
                          for printing from       
                          physical signing and    
                          execution.              
  -----------------------------------------------------------------------

The system records official numbering; it does not independently
generate or rearrange official numbers until the office's conventions
have been validated.

## 7.9 Scanned Document Upload and Archiving

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-UP-001               The system shall allow  Must
                          authorized users to     
                          upload scanned          
                          documents from their    
                          computers.              

  FR-UP-002               The system shall        Must
                          support PDF uploads.    

  FR-UP-003               The system shall        Must
                          support uploads         
                          containing either one   
                          document or multiple    
                          documents.              

  FR-UP-004               The system shall        Must
                          associate uploaded      
                          documents with the      
                          appropriate client,     
                          request, and document   
                          record.                 

  FR-UP-005               The system shall        Must
                          preserve the original   
                          uploaded scanned file.  

  FR-UP-006               The system shall allow  Must
                          authorized users to     
                          review uploaded files   
                          and their associations. 
  -----------------------------------------------------------------------

Reliable upload and correct association are essential. Automatic
boundary detection and splitting of multiple documents in a PDF may be
implemented as an enhancement if technically feasible.

## 7.10 OCR and Metadata Extraction

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-OCR-001              The system shall        Must
                          process uploaded        
                          scanned documents using 
                          OCR technology.         

  FR-OCR-002              The system shall        Must
                          extract searchable text 
                          from supported scanned  
                          documents.              

  FR-OCR-003              The system shall        Must
                          attempt to identify     
                          relevant document       
                          metadata from extracted 
                          text.                   

  FR-OCR-004              The system shall allow  Must
                          authorized users to     
                          review extracted text   
                          and metadata.           

  FR-OCR-005              The system shall allow  Must
                          authorized users to     
                          correct inaccurate      
                          extracted metadata.     

  FR-OCR-006              The system shall        Must
                          preserve the original   
                          scanned file separately 
                          from OCR-extracted      
                          text.                   

  FR-OCR-007              The system shall store  Must
                          verified metadata with  
                          the archived document.  

  FR-OCR-008              The system shall        Must
                          indicate when OCR       
                          processing or metadata  
                          verification is         
                          incomplete.             
  -----------------------------------------------------------------------

OCR output must not automatically be treated as verified information.
Human review is required before metadata is considered verified.

## 7.11 Digital Archive and Document Search

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-ARC-001              The system shall store  Must
                          signed and verified     
                          scanned documents in a  
                          centralized digital     
                          archive.                

  FR-ARC-002              The system shall        Must
                          distinguish documents   
                          awaiting archiving from 
                          documents successfully  
                          archived.               

  FR-SRCH-001             The system shall allow  Must
                          authorized users to     
                          search archived         
                          documents by client     
                          name.                   

  FR-SRCH-002             The system shall allow  Must
                          searches by document    
                          type.                   

  FR-SRCH-003             The system shall allow  Must
                          searches by document    
                          date.                   

  FR-SRCH-004             The system shall allow  Must
                          searches by official    
                          document number and     
                          available register      
                          references.             

  FR-SRCH-005             The system shall        Must
                          support searching       
                          through OCR-extracted   
                          text.                   

  FR-SRCH-006             The system shall allow  Must
                          authorized users to     
                          view and retrieve       
                          archived documents.     
  -----------------------------------------------------------------------

## 7.12 Audit Records and Reports

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-AUD-001              The system shall record Must
                          important activities,   
                          including document      
                          submission, review,     
                          approval, revision, and 
                          archiving.              

  FR-AUD-002              The system shall record Must
                          the user and date       
                          associated with         
                          relevant activities.    

  FR-REP-001              The system shall        Should
                          provide basic reports   
                          about requests and      
                          document statuses.      

  FR-REP-002              The system shall allow  Should
                          authorized users to     
                          export supported        
                          reports to Excel.       

  FR-REP-003              The system shall allow  Should
                          authorized users to     
                          export supported        
                          reports to PDF.         
  -----------------------------------------------------------------------

Reports will be exported for manual submission where required. Direct
integration with government or judicial systems is outside the MVP.

## 7.13 Storage and Backup

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-STOR-001             The system shall store  Must
                          uploaded and generated  
                          documents in an         
                          organized storage       
                          structure.              

  FR-STOR-002             The system shall        Must
                          maintain a centralized  
                          repository accessible   
                          to authorized users.    

  FR-STOR-003             The system shall        Must
                          support backup of       
                          important system        
                          records and files.      

  FR-STOR-004             The system shall        Should
                          support cloud           
                          synchronization if      
                          included in the         
                          approved deployment     
                          design.                 

  FR-STOR-005             The system shall not    Must
                          automatically delete    
                          local copies after      
                          synchronization.        

  FR-STOR-006             The system shall        Must
                          restrict local file     
                          offloading or deletion  
                          to authorized           
                          personnel.              
  -----------------------------------------------------------------------

Cloud synchronization and backup details will be determined during
architecture and deployment planning. Upload or synchronization success
does not authorize deletion of the office's local copy.

------------------------------------------------------------------------

# VIII. Non-Functional Requirements

Priority labels have the same meaning as in Section VII.

## 8.1 Security

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-SEC-001             The system shall        Must
                          require authentication  
                          before users can access 
                          protected features.     

  NFR-SEC-002             The system shall        Must
                          enforce role-based      
                          access control for      
                          Office Staff and        
                          Attorney.               

  NFR-SEC-003             The system shall        Must
                          protect user passwords  
                          using secure password   
                          hashing.                

  NFR-SEC-004             The system shall        Must
                          prevent unauthorized    
                          access to confidential  
                          client information and  
                          legal documents.        

  NFR-SEC-005             The system shall        Must
                          validate uploaded files 
                          and restrict            
                          unsupported file types. 

  NFR-SEC-006             The system shall        Must
                          maintain records of     
                          important user          
                          activities.             

  NFR-SEC-007             The system shall        Must
                          protect document files  
                          against unauthorized    
                          modification or         
                          deletion.               
  -----------------------------------------------------------------------

## 8.2 Usability

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-USE-001             The system shall        Must
                          provide a clear and     
                          consistent user         
                          interface.              

  NFR-USE-002             The system shall        Must
                          organize client         
                          records, requests,      
                          documents, and archives 
                          in an understandable    
                          manner.                 

  NFR-USE-003             The system shall        Must
                          provide understandable  
                          status indicators for   
                          document workflows.     

  NFR-USE-004             The system shall        Must
                          provide clear feedback  
                          when an operation       
                          succeeds or fails.      

  NFR-USE-005             The system shall allow  Must
                          authorized users to     
                          locate records through  
                          search functionality.   

  NFR-USE-006             The document editor     Must
                          shall provide familiar  
                          basic text-formatting   
                          controls.               
  -----------------------------------------------------------------------

## 8.3 Performance

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-PER-001             The system shall        Must
                          respond to ordinary     
                          user interactions       
                          within an acceptable    
                          time under normal       
                          operating conditions.   

  NFR-PER-002             The system shall        Must
                          support searching and   
                          retrieving stored       
                          records without         
                          unnecessary delays.     

  NFR-PER-003             The system shall        Should
                          process uploaded        
                          documents without       
                          unnecessarily blocking  
                          other system            
                          operations.             

  NFR-PER-004             The system shall        Should
                          provide progress or     
                          status feedback during  
                          lengthy file uploads    
                          and OCR operations.     
  -----------------------------------------------------------------------

Exact response-time and file-size targets shall be established through
testing and representative documents.

## 8.4 Reliability and Data Integrity

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-REL-001             The system shall        Must
                          preserve saved client,  
                          request, and document   
                          records during normal   
                          operation.              

  NFR-REL-002             The system shall        Must
                          preserve previous       
                          document versions when  
                          revisions are made.     

  NFR-REL-003             The system shall        Must
                          maintain the            
                          association between     
                          documents, clients, and 
                          requests.               

  NFR-REL-004             The system shall retain Must
                          original scanned files  
                          separately from         
                          OCR-extracted content.  

  NFR-REL-005             The system shall        Must
                          provide a backup        
                          mechanism for important 
                          system data and files.  

  NFR-REL-006             The system shall        Must
                          indicate incomplete or  
                          failed upload and OCR   
                          operations.             
  -----------------------------------------------------------------------

## 8.5 Compatibility

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-COMP-001            The system shall be     Must
                          accessible through      
                          supported desktop web   
                          browsers.               

  NFR-COMP-002            The system shall        Must
                          support the document    
                          formats selected for    
                          the approved            
                          implementation.         

  NFR-COMP-003            The system shall        Must
                          support PDF files       
                          produced by the law     
                          office's scanning       
                          process.                

  NFR-COMP-004            The system shall        Must
                          provide a document      
                          output suitable for the 
                          office's printing       
                          workflow.               
  -----------------------------------------------------------------------

## 8.6 Maintainability

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-MNT-001             The system shall use a  Should
                          modular structure to    
                          separate major          
                          functional components.  

  NFR-MNT-002             The system shall        Should
                          maintain organized      
                          source code and         
                          database structures.    

  NFR-MNT-003             The system shall allow  Should
                          future modification of  
                          document categories,    
                          templates, and          
                          supported metadata      
                          fields.                 

  NFR-MNT-004             The system shall        Should
                          provide sufficient      
                          technical documentation 
                          to support future       
                          maintenance.            
  -----------------------------------------------------------------------

## 8.7 Privacy and Confidentiality

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  NFR-PRI-001             The system shall        Must
                          restrict client and     
                          legal document          
                          information to          
                          authorized internal     
                          users.                  

  NFR-PRI-002             The system shall avoid  Must
                          exposing confidential   
                          documents through       
                          publicly accessible     
                          links.                  

  NFR-PRI-003             The system shall handle Must
                          stored client           
                          information in          
                          accordance with         
                          applicable              
                          data-protection         
                          requirements.           

  NFR-PRI-004             The system shall        Must
                          restrict access to      
                          archived documents      
                          according to assigned   
                          permissions.            
  -----------------------------------------------------------------------

**Open measurement items:** performance targets, maximum upload size,
supported browsers and file formats, backup frequency, recovery
expectations, and detailed access permissions must be defined during
design and validation.

------------------------------------------------------------------------

# IX. Conceptual Database Model

This section is a conceptual starting point, not a final
implementation-ready schema. The logical ERD must be refined before
database implementation.

## 9.1 Proposed Entities and Attributes

### USERS

-   `user_id` --- Primary Key
-   `role_id` --- Foreign Key
-   `full_name`
-   `username`
-   `password_hash`
-   `account_status`
-   `created_at`

### ROLES

-   `role_id` --- Primary Key
-   `role_name`

### CLIENTS

-   `client_id` --- Primary Key
-   `full_name`
-   `contact_number`
-   `address`
-   `created_at`
-   `updated_at`

### REQUESTS

-   `request_id` --- Primary Key
-   `client_id` --- Foreign Key
-   `request_type`
-   `request_date`
-   `request_status`
-   `remarks`
-   `created_by` --- Foreign Key to USERS

### REQUEST_DOCUMENTS

-   `request_document_id` --- Primary Key
-   `request_id` --- Foreign Key
-   `template_id` --- Nullable Foreign Key
-   `document_title`
-   `document_type`
-   `document_status`
-   `official_document_number` --- Nullable in the conceptual draft;
    authoritative location must be decided
-   `created_at`
-   `updated_at`

### TEMPLATES

-   `template_id` --- Primary Key
-   `template_name`
-   `document_type`
-   `category`
-   `file_location`
-   `uploaded_by` --- Foreign Key to USERS
-   `created_at`
-   `updated_at`

### DOCUMENT_VERSIONS

-   `version_id` --- Primary Key
-   `request_document_id` --- Foreign Key
-   `version_number`
-   `file_location`
-   `version_status`
-   `created_by` --- Foreign Key to USERS
-   `created_at`

### DOCUMENT_REVIEWS

-   `review_id` --- Primary Key
-   `version_id` --- Foreign Key
-   `attorney_id` --- Foreign Key to USERS
-   `review_status`
-   `comments`
-   `reviewed_at`

### DOCUMENT_FILES

-   `file_id` --- Primary Key
-   `request_document_id` --- Foreign Key
-   `version_id` --- Nullable Foreign Key
-   `file_type`
-   `file_location`
-   `uploaded_by` --- Foreign Key to USERS
-   `uploaded_at`

### ARCHIVE_METADATA

-   `metadata_id` --- Primary Key
-   `file_id` --- Foreign Key
-   `official_document_number`
-   `document_date`
-   `document_type`
-   `book_number` --- Nullable
-   `page_number` --- Nullable
-   `series_year` --- Nullable
-   `verification_status`
-   `verified_by` --- Nullable Foreign Key to USERS
-   `verified_at` --- Nullable

### OCR_RESULTS

-   `ocr_id` --- Primary Key
-   `file_id` --- Foreign Key
-   `extracted_text`
-   `processing_status`
-   `processed_at`

### ACTIVITY_LOGS

-   `log_id` --- Primary Key
-   `user_id` --- Foreign Key
-   `activity_type`
-   `description`
-   `related_record_type`
-   `related_record_id`
-   `created_at`

## 9.2 Proposed Relationships

  -----------------------------------------------------------------------
  Relationship            Cardinality             Explanation
  ----------------------- ----------------------- -----------------------
  ROLES → USERS           One-to-Many             One role can be
                                                  assigned to multiple
                                                  user accounts.

  CLIENTS → REQUESTS      One-to-Many             A client may submit
                                                  multiple requests.

  USERS → REQUESTS        One-to-Many             A user may create
                                                  multiple requests.

  REQUESTS →              One-to-Many             A request may contain
  REQUEST_DOCUMENTS                               multiple documents.

  TEMPLATES →             One-to-Many             A template may be used
  REQUEST_DOCUMENTS                               to prepare multiple
                                                  documents.

  REQUEST_DOCUMENTS →     One-to-Many             A document may have
  DOCUMENT_VERSIONS                               multiple versions.

  USERS →                 One-to-Many             A user may create
  DOCUMENT_VERSIONS                               multiple versions.

  DOCUMENT_VERSIONS →     One-to-Many             A version may have
  DOCUMENT_REVIEWS                                multiple review records
                                                  over its lifecycle.

  USERS →                 One-to-Many             The Attorney may review
  DOCUMENT_REVIEWS                                multiple versions.

  REQUEST_DOCUMENTS →     One-to-Many             A document may have
  DOCUMENT_FILES                                  multiple associated
                                                  files.

  DOCUMENT_VERSIONS →     One-to-Many             A version may have
  DOCUMENT_FILES                                  associated generated or
                                                  supporting files.

  DOCUMENT_FILES →        One-to-Many             A file may have
  OCR_RESULTS                                     multiple OCR processing
                                                  attempts.

  DOCUMENT_FILES →        One-to-One, initially   An archived file has
  ARCHIVE_METADATA                                its verified metadata
                                                  record.

  USERS → DOCUMENT_FILES  One-to-Many             A user may upload
                                                  multiple files.

  USERS → TEMPLATES       One-to-Many             A user may upload
                                                  multiple templates.

  USERS → ACTIVITY_LOGS   One-to-Many             A user may generate
                                                  multiple activity
                                                  records.
  -----------------------------------------------------------------------

## 9.3 Conceptual ERD (Mermaid)

``` mermaid
erDiagram
    ROLES ||--o{ USERS : assigns
    USERS ||--o{ REQUESTS : creates
    CLIENTS ||--o{ REQUESTS : submits
    REQUESTS ||--|{ REQUEST_DOCUMENTS : contains
    TEMPLATES o|--o{ REQUEST_DOCUMENTS : used_for
    REQUEST_DOCUMENTS ||--|{ DOCUMENT_VERSIONS : has
    USERS ||--o{ DOCUMENT_VERSIONS : creates
    DOCUMENT_VERSIONS ||--o{ DOCUMENT_REVIEWS : receives
    USERS ||--o{ DOCUMENT_REVIEWS : performs
    REQUEST_DOCUMENTS ||--o{ DOCUMENT_FILES : has
    DOCUMENT_VERSIONS o|--o{ DOCUMENT_FILES : associated_with
    DOCUMENT_FILES ||--o{ OCR_RESULTS : processes
    DOCUMENT_FILES ||--o| ARCHIVE_METADATA : has
    USERS ||--o{ DOCUMENT_FILES : uploads
    USERS ||--o{ TEMPLATES : uploads
    USERS ||--o{ ACTIVITY_LOGS : generates
```

## 9.4 Important Database Design Decisions and Refinements

1.  One client can have multiple requests; do not duplicate the client
    profile for each visit.
2.  One request can contain multiple documents; each document has its
    own status and version history.
3.  Templates must be separate from generated documents. Updating a
    template must not automatically change documents already created
    from it.
4.  Revisions must create new versions rather than overwrite earlier
    versions.
5.  Original scanned files must be stored separately from OCR results.
6.  OCR metadata must record verification status, verifier, and
    verification time.
7.  Request completion is based on physical signing, not digital archive
    completion.
8.  Official numbering remains under the office's control.

**Logical-design items still to resolve:** - The conceptual draft
contains the official document number in both REQUEST_DOCUMENTS and
ARCHIVE_METADATA. Choose one authoritative location and avoid
inconsistent duplicate values. - Record physical signing date and
responsible user explicitly rather than relying only on a general
status. - Decide whether a single archive file may represent multiple
logical documents after a multi-document PDF is uploaded and split. -
Define optionality and cardinality precisely, including whether every
request must initially contain at least one document. - Define
constraints for unique usernames, version numbers per document, status
values, file references, and deletion/retention. - Consider whether role
permissions need a separate permissions table or whether a simpler
role-based model is sufficient for the MVP.

------------------------------------------------------------------------

# X. Assumptions and Unresolved Questions

## 10.1 Confirmed Decisions

  -----------------------------------------------------------------------
  Area                                Confirmed decision
  ----------------------------------- -----------------------------------
  System users                        Office Staff and Attorney

  Client access                       Clients do not have system
                                      accounts.

  Attorney count                      One Attorney at this specific law
                                      office.

  Client management                   One client may have multiple
                                      requests.

  Request structure                   One request may contain multiple
                                      documents.

  Document revisions                  Revisions create new versions;
                                      previous versions are preserved.

  Attorney review                     Attorney can leave comments and
                                      request corrections.

  Printing                            Authorized staff may print
                                      Attorney-approved documents.

  Physical signing                    Attorney performs required wet-ink
                                      signing.

  Scanning                            Signed documents are scanned using
                                      a physical scanner.

  Upload                              Scanned PDF files are uploaded from
                                      a computer.

  OCR                                 OCR extracts text and attempts
                                      metadata extraction; a human
                                      verifies results.

  Archiving                           Digital archiving requires upload,
                                      OCR processing, and metadata
                                      verification.

  Request completion                  Based on required physical
                                      signatures, even if archiving
                                      remains pending.

  Official numbering                  The system records numbers assigned
                                      through the existing office
                                      process.

  Templates                           Staff should be able to upload,
                                      organize, create, and manage
                                      templates.

  Document editor                     An embedded rich-text editor is
                                      planned.

  Reports                             Excel and PDF exports are in the
                                      planned scope.

  External integration                Direct government or judicial API
                                      integration is excluded.

  Local files                         Synchronization must not
                                      automatically delete local copies.
  -----------------------------------------------------------------------

## 10.2 Proposed Design Decisions Awaiting Validation

  -----------------------------------------------------------------------
  ID                      Proposed decision       Validation needed
  ----------------------- ----------------------- -----------------------
  X-PD-001                Attorney receives       Confirm with project
                          user-management         leader and Attorney.
                          permission instead of   
                          adding a third          
                          Administrator role.     

  X-PD-002                Initial Attorney        Confirm setup and
                          account is established  responsibility.
                          through secure          
                          first-run setup.        

  X-PD-003                A document version may  Confirm actual review
                          have multiple Attorney  process.
                          review records.         

  X-PD-004                System supports         Validate using scanner
                          individual and          output.
                          multi-document PDF      
                          uploads.                

  X-PD-005                System attempts to      Test feasibility.
                          detect boundaries in    
                          multi-document PDFs,    
                          with human review and   
                          splitting where needed. 

  X-PD-006                Embedded editor         Test actual templates.
                          supports basic          
                          formatting and tables.  

  X-PD-007                OCR metadata is stored  Validate metadata
                          separately from the     fields with Attorney.
                          original scanned PDF.   
  -----------------------------------------------------------------------

## 10.3 Unresolved Operational Questions

  -----------------------------------------------------------------------
  ID                      Question                Why it matters
  ----------------------- ----------------------- -----------------------
  X-UQ-001                What formats are used   Determines template
                          by existing templates:  import and editor
                          DOCX, DOC, PDF, or a    compatibility.
                          mixture?                

  X-UQ-002                Are signed documents    Determines upload and
                          scanned individually or splitting workflow.
                          are several sometimes   
                          scanned into one PDF?   

  X-UQ-003                What exact metadata     Determines archive
                          fields must be stored   structure and search
                          for each archived       filters.
                          document?               

  X-UQ-004                What official numbering Prevents incorrect
                          and register-reference  handling of official
                          conventions does the    records.
                          office follow?          

  X-UQ-005                Does the office need to Determines whether
                          track whether exported  submission tracking is
                          reports have been       needed.
                          submitted externally?   

  X-UQ-006                What should happen when Determines cancellation
                          a request or document   and retention behavior.
                          is cancelled or         
                          abandoned?              

  X-UQ-007                Which users may manage  Determines detailed
                          templates and archived  permissions.
                          files?                  

  X-UQ-008                Where should uploaded   Affects deployment,
                          files and OCR           security, storage, and
                          processing be hosted?   performance.

  X-UQ-009                What backup frequency   Determines backup and
                          and recovery            recovery design.
                          expectations does the   
                          office require?         

  X-UQ-010                Does the office have    Determines whether
                          existing digital        historical data
                          records that need       migration is needed.
                          importing?              
  -----------------------------------------------------------------------

## 10.4 Technical Feasibility Questions

  -----------------------------------------------------------------------
  ID                      Technical matter        Planned investigation
  ----------------------- ----------------------- -----------------------
  X-TF-001                Rich-text editor and    Test whether the editor
                          document formatting     preserves formatting of
                                                  actual legal templates.

  X-TF-002                DOCX import/export      Evaluate compatibility
                                                  and formatting
                                                  preservation.

  X-TF-003                OCR accuracy            Test representative
                                                  scans with different
                                                  scan qualities.

  X-TF-004                Metadata extraction     Test extraction of
                                                  document numbers,
                                                  dates, parties, and
                                                  applicable register
                                                  details.

  X-TF-005                Multi-document PDF      Evaluate whether
                          splitting               document boundaries can
                                                  be detected reliably.

  X-TF-006                File storage and        Evaluate secure
                          synchronization         storage, backup, and
                                                  synchronization
                                                  options.

  X-TF-007                Search performance      Test metadata and OCR
                                                  full-text search with
                                                  representative records.
  -----------------------------------------------------------------------

## 10.5 Initial Assumptions and Limitations

1.  The MVP is for internal law-office use.
2.  The system will not replace physical signing or the official bound
    Notarial Register.
3.  The system will not make legal decisions or automatically approve
    documents.
4.  OCR may contain errors and requires human verification.
5.  The original scanned PDF will be preserved.
6.  The system will not automatically delete local files after
    synchronization.
7.  Advanced editor features and automatic PDF splitting depend on
    technical feasibility.
8.  Unconfirmed operational procedures will be validated before becoming
    mandatory business rules.

## 10.6 Handling Unresolved Questions

-   Core workflow questions must be resolved before finalizing the
    affected feature.
-   Technical feasibility questions should be investigated through
    prototypes and tests.
-   Optional enhancements should be deferred if they are not essential
    to the MVP.
-   Legal and official procedures must be confirmed by the Attorney.
-   Unconfirmed requirements must not silently become approved features.

------------------------------------------------------------------------

# XI. Requirements Traceability Matrix

## 11.1 Project Objective Reference

-   **O1:** Centralize client records, requests, templates, document
    versions, and signed archives.
-   **O2:** Provide document preparation, Attorney review, correction,
    and approval workflows.
-   **O3:** Preserve document versions and review history.
-   **O4:** Integrate OCR for text extraction and metadata assistance.
-   **O5:** Provide searchable digital document retrieval.
-   **O6:** Implement access controls and activity records.
-   **O7:** Support digital archiving while retaining physical
    originals.

## 11.2 Objective-to-Requirement Mapping

  -----------------------------------------------------------------------
  Objective               Related functional      Expected result
                          requirements            
  ----------------------- ----------------------- -----------------------
  O1 --- Centralized      FR-CL-001--005,         Organized client,
  records                 FR-REQ-001--006,        request, template, and
                          FR-TEMP-001--006,       archive records.
                          FR-ARC-001--002         

  O2 --- Document         FR-DOC-001--008,        Documents can be
  workflow                FR-REV-001--008,        prepared, reviewed,
                          FR-SIG-001--006         corrected, approved,
                                                  printed, and physically
                                                  signed.

  O3 --- Version          FR-VER-001--005         Previous versions and
  preservation                                    review history remain
                                                  accessible.

  O4 --- OCR integration  FR-UP-001--006,         Scanned documents are
                          FR-OCR-001--008         processed and
                                                  searchable text and
                                                  metadata are extracted
                                                  and verified.

  O5 --- Search and       FR-SRCH-001--006        Authorized users can
  retrieval                                       locate and retrieve
                                                  archived documents.

  O6 --- Security and     FR-AUTH-001--006,       User access is
  accountability          FR-AUD-001--002         controlled and
                                                  important activities
                                                  are recorded.

  O7 --- Digital          FR-ARC-001--002,        Signed documents are
  archiving               FR-UP-001--006,         digitally archived
                          FR-OCR-001--008,        while physical
                          FR-STOR-001--006        originals remain in the
                                                  office.
  -----------------------------------------------------------------------

## 11.3 Non-Functional Requirement Mapping

  -----------------------------------------------------------------------
  Quality area            Related requirements    Purpose
  ----------------------- ----------------------- -----------------------
  Security                NFR-SEC-001--007        Protect accounts,
                                                  records, and documents.

  Usability               NFR-USE-001--006        Make the system
                                                  understandable and
                                                  practical for office
                                                  users.

  Performance             NFR-PER-001--004        Keep ordinary
                                                  operations and document
                                                  processing responsive.

  Reliability             NFR-REL-001--006        Preserve records and
                                                  handle failures
                                                  appropriately.

  Compatibility           NFR-COMP-001--004       Support selected
                                                  browsers, file formats,
                                                  and printing workflow.

  Maintainability         NFR-MNT-001--004        Make the system easier
                                                  to update and maintain.

  Privacy                 NFR-PRI-001--004        Protect confidential
                                                  client and legal
                                                  information.
  -----------------------------------------------------------------------

## 11.4 Requirement-to-System-Module Mapping

  System module                          Main requirements   MVP status
  -------------------------------------- ------------------- ------------------------------------
  Authentication and access management   FR-AUTH, NFR-SEC    Core
  Client management                      FR-CL               Core
  Request management                     FR-REQ              Core
  Template management                    FR-TEMP             Core
  Document editor                        FR-DOC              Core
  Review and approval                    FR-REV              Core
  Version management                     FR-VER              Core
  Printing and signing records           FR-SIG              Core
  Scanned document upload                FR-UP               Core
  OCR and metadata                       FR-OCR              Core, basic implementation first
  Digital archive                        FR-ARC              Core
  Search and retrieval                   FR-SRCH             Core
  Audit records                          FR-AUD              Basic implementation
  Reports and exports                    FR-REP              Enhancement
  Storage and backup                     FR-STOR             Essential storage and backup first

## 11.5 Traceability and Change Management

The development team shall use this matrix to:

1.  Verify that each project objective is addressed by one or more
    system requirements.
2.  Identify which modules implement each requirement.
3.  Track whether requirements have been designed, implemented, and
    tested.
4.  Identify requirements affected by proposed changes.
5.  Prevent features unrelated to approved project objectives from
    unnecessarily expanding the MVP.

When a new feature is proposed, determine whether it supports an
approved objective, whether it is necessary for the MVP, and whether it
affects schedule, architecture, or existing requirements.

------------------------------------------------------------------------

# XII. MVP Implementation Strategy

The MVP is intended to deliver the smallest reliable system that
demonstrates the project's central purpose. It is not an excuse to omit
the core document lifecycle or OCR objective.

## 12.1 Phase 1 --- Core MVP

1.  Authentication and user permissions.
2.  Client and request management.
3.  Template upload and organization.
4.  Embedded document editor with basic formatting.
5.  Attorney review, comments, and approval.
6.  Document version history.
7.  Printing and recording physical signing.
8.  Scanned PDF upload and association.
9.  Basic OCR text extraction and human verification.
10. Digital archive and basic search.

## 12.2 Phase 2 --- Important Enhancements

-   Advanced OCR metadata extraction.
-   Multi-document PDF boundary detection and splitting.
-   Excel/PDF reports.
-   Detailed audit records.
-   More advanced search filters.

## 12.3 Phase 3 --- Deployment and Operational Improvements

-   Cloud synchronization.
-   Automated backup improvements.
-   File integrity verification.
-   Administrative storage and offloading controls.

## 12.4 Recommended Development Order

1.  Authentication and roles.
2.  Client management.
3.  Request management.
4.  Template management.
5.  Document editor and document preparation.
6.  Attorney review and versioning.
7.  Printing/signing records.
8.  Scanned file upload.
9.  OCR proof of concept and integration.
10. Archive metadata verification and search.
11. Audit, reporting, backup, and deployment refinements.

OCR and document-editor feasibility should be investigated early, in
parallel with foundational design. Do not postpone all OCR
experimentation until the end because OCR is central to the project
title and objective.

------------------------------------------------------------------------

# XIII. Next Design and Development Activities

The initial Systems Analysis baseline is complete. The next activities
are:

1.  **Logical database design:** finalize entities, attributes, data
    types, primary keys, foreign keys, uniqueness, nullability,
    constraints, and normalization.
2.  **Use-case modeling:** define interactions for Office Staff and
    Attorney.
3.  **Role-permission matrix:** specify permissions for each system
    module and action.
4.  **Workflow/state modeling:** define valid document and request
    status transitions.
5.  **Wireframes:** design login, dashboard, client profile, request
    details, template management, editor, review, upload, archive, and
    search screens.
6.  **Architecture and technology selection:** choose application
    framework, database, file storage, OCR engine, editor, and
    deployment model based on project constraints.
7.  **Proofs of concept:** test OCR on representative scans and the
    editor with representative legal templates.
8.  **Implementation and testing:** build the MVP in small modules and
    verify each requirement against the RTM.

Do not begin by coding every module at once. Finalize the database and
core workflow design sufficiently, then implement incrementally.

------------------------------------------------------------------------

# XIV. Development Handoff Prompt for Another AI

The following prompt may be supplied to an AI development assistant
together with this document:

> You are acting as a senior systems analyst and software architect
> assisting an undergraduate IT capstone team in developing the Jumamil
> Law System described in this document.
>
> Treat this document as the project baseline. Read it fully before
> proposing architecture or code. Do not silently change approved scope,
> invent law-office workflows, or add features just because they are
> common in other legal systems.
>
> The immediate task is to help complete the logical database design.
> Start by reviewing the conceptual entities and relationships in
> Section IX. Identify inconsistencies, normalization concerns, missing
> attributes, and unclear cardinalities. Explain each issue and propose
> a correction, clearly labeling it as a recommendation rather than a
> confirmed requirement.
>
> Do not generate the entire application in one response. Work
> iteratively: 1. Explain the design decision and why it matters. 2.
> Present a small, reviewable artifact. 3. Identify assumptions and
> unresolved questions. 4. Wait for the project team to review before
> treating the design as final. 5. Keep a concise project checkpoint
> that can be reused in future sessions.
>
> Prioritize the MVP. Preserve document version history, attorney
> comments, original scanned files, OCR results, and verified metadata.
> Never treat OCR output as verified without human review. Never replace
> physical signing or official numbering with an invented automated
> process.
>
> The embedded editor and OCR are technical risks. Recommend early
> proofs of concept using representative office templates and scanned
> documents before committing to a technology.
>
> Use beginner-friendly explanations. The student is learning systems
> analysis and programming and wants to understand the reasoning, not
> merely receive code. When coding eventually begins, use modular,
> testable increments and explain how each part connects to the approved
> requirements.
>
> If a requirement is unclear, ask one focused question at a time or
> record it as unresolved. Do not overwhelm the team with a large
> questionnaire.
>
> Your first deliverable should be a reviewed logical database design
> proposal, not application code.

------------------------------------------------------------------------

## End of Document

**Document status:** Consolidated initial Systems Analysis and
Development Handoff baseline. Sections I--XI were reviewed and approved
in the project discussion. The conceptual ERD and proposed design
decisions still require detailed refinement and operational/technical
validation before implementation.
