/** CFile**********************************************************

  FileName    [run_abc.h]

  SystemName  [A New Tool for Boolean Circuit Analysis and Synthesis]

  Date        [Ver. 1.0. Started - August 7, 2024.]

  Revision    [Initial version.]

  Note        [The structure `Extra_FileReader_t_`, the enum `Extra_CharType_t`,
               the macros `EXTRA_BUFFER_SIZE`, `EXTRA_OFFSET_SIZE`, and
               `EXTRA_MINIMUM`, the function `Extra_FileReaderAllocFromString`,
               which is a modified version of `Extra_FileReaderAlloc`, and the
               functions `Io_ReadBenchNetwork`, `Io_WriteBenchOneNode`, and
               `Io_WriteBenchOne` used in this file were adapted from the ABC:
               Logic synthesis and verification system, written by Alan Mishchenko
               at UC Berkeley. Specifically, `Extra_FileReader_t_`, `Extra_CharType_t`,
               `EXTRA_BUFFER_SIZE`, `EXTRA_OFFSET_SIZE`, and `EXTRA_MINIMUM` were
               adapted from `extraUtilReader.c`, `Io_ReadBenchNetwork` was copied
               from `ioReadBench.c`, and `Io_WriteBenchOneNode` and `Io_WriteBenchOne`
               were copied from `ioWriteBench.c`.]

***********************************************************************/

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>

#include <abc/src/misc/util/abc_global.h>
#include <abc/src/misc/extra/extra.h>
#include <abc/src/misc/vec/vec.h>
#include <abc/src/base/abc/abc.h>
#include <abc/src/base/main/main.h>
#include <abc/src/base/main/mainInt.h>

#define EXTRA_BUFFER_SIZE        4*1048576    // 1M   - size of the data chunk stored in memory
#define EXTRA_OFFSET_SIZE           4096    // 4K   - load new data when less than this is left

#define EXTRA_MINIMUM(a,b)       (((a) < (b))? (a) : (b))

/**
The structure of this file was adapted from extraUtilReader.c
from the ABC: Logic synthesis and verification system, written
by Alan Mishchenko at UC Berkeley.
**/
struct Extra_FileReader_t_
{
    // the input file
    char *           pFileName;     // the input file name
    FILE *           pFile;         // the input file pointer
    int              nFileSize;     // the total number of bytes in the file
    int              nFileRead;     // the number of bytes currently read from file
    // info about processing different types of input chars
    char             pCharMap[256]; // the character map
    // temporary storage for data
    char *           pBuffer;       // the buffer
    int              nBufferSize;   // the size of the buffer
    char *           pBufferCur;    // the current reading position
    char *           pBufferEnd;    // the first position not used by currently loaded data
    char *           pBufferStop;   // the position where loading new data will be done
    // tokens given to the user
    Vec_Ptr_t *      vTokens;       // the vector of tokens returned to the user
    Vec_Int_t *      vLines;        // the vector of line numbers for each token
    int              nLineCounter;  // the counter of lines processed
    // status of the parser
    int              fStop;         // this flag goes high when the end of file is reached
};

// character types
typedef enum {
    EXTRA_CHAR_COMMENT,  // a character that begins the comment
    EXTRA_CHAR_NORMAL,   // a regular character
    EXTRA_CHAR_STOP,     // a character that delimits a series of tokens
    EXTRA_CHAR_CLEAN     // a character that should be cleaned
} Extra_CharType_t;


Extra_FileReader_t *Extra_FileReaderAllocFromString(char *pFileContent, char *pCharsComment, char *pCharsStop, char *pCharsClean)
{
    Extra_FileReader_t *p;
    char *pChar;
    int nCharsToRead;

    // start the file reader
    p = ABC_ALLOC(Extra_FileReader_t, 1);
    memset(p, 0, sizeof(Extra_FileReader_t));
    p->pFileName = "filename.bench"; // No file name since content is provided directly
    p->pFile = NULL; // No file pointer since content is provided directly

    // set the character map
    memset(p->pCharMap, EXTRA_CHAR_NORMAL, 256);
    for (pChar = pCharsComment; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_COMMENT;
    for (pChar = pCharsStop; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_STOP;
    for (pChar = pCharsClean; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_CLEAN;

    // get the content size, in bytes
    p->nFileSize = strlen(pFileContent);

    // allocate the buffer
    p->pBuffer = ABC_ALLOC(char, EXTRA_BUFFER_SIZE + 1);
    p->nBufferSize = EXTRA_BUFFER_SIZE;
    p->pBufferCur = p->pBuffer;

    // determine how many chars to read
    nCharsToRead = EXTRA_MINIMUM(p->nFileSize, EXTRA_BUFFER_SIZE);

    // load the first part into the buffer
    strncpy(p->pBuffer, pFileContent, nCharsToRead);
    p->nFileRead = nCharsToRead;

    // set the pointers to the end and the stopping point
    p->pBufferEnd = p->pBuffer + nCharsToRead;
    p->pBufferStop = (p->nFileRead == p->nFileSize) ? p->pBufferEnd : p->pBuffer + EXTRA_BUFFER_SIZE - EXTRA_OFFSET_SIZE;

    // start the arrays
    p->vTokens = Vec_PtrAlloc(100);
    p->vLines = Vec_IntAlloc(100);
    p->nLineCounter = 1; // 1-based line counting

    return p;
}

Abc_Ntk_t * Io_ReadBenchNetwork( Extra_FileReader_t * p )
{
    ProgressBar * pProgress;
    Vec_Ptr_t * vTokens;
    Abc_Ntk_t * pNtk;
    Abc_Obj_t * pNode, * pNet;
    Vec_Str_t * vString;
    unsigned uTruth[2048];
    char * pType, ** ppNames, * pString;
    int iLine, nNames, nDigits, fLutsPresent = 0;

    // allocate the empty network
    pNtk = Abc_NtkStartRead( Extra_FileReaderGetFileName(p) );
    pNtk->nConstrs = 0;

    // go through the lines of the file
    vString = Vec_StrAlloc( 100 );
    pProgress = Extra_ProgressBarStart( stdout, Extra_FileReaderGetFileSize(p) );
    for ( iLine = 0; (vTokens = (Vec_Ptr_t *)Extra_FileReaderGetTokens(p)); iLine++ )
    {
        Extra_ProgressBarUpdate( pProgress, Extra_FileReaderGetCurPosition(p), NULL );

        if ( vTokens->nSize == 1 )
        {
            printf( "%s: Wrong input file format.\n", Extra_FileReaderGetFileName(p) );
            Vec_StrFree( vString );
            Abc_NtkDelete( pNtk );
            return NULL;
        }

        // get the type of the line
        if ( strncmp( (char *)vTokens->pArray[0], "INPUT", 5 ) == 0 )
            Io_ReadCreatePi( pNtk, (char *)vTokens->pArray[1] );
        else if ( strncmp( (char *)vTokens->pArray[0], "OUTPUT", 5 ) == 0 )
            Io_ReadCreatePo( pNtk, (char *)vTokens->pArray[1] );
        else
        {
            // get the node name and the node type
            pType = (char *)vTokens->pArray[1];
            if ( strncmp(pType, "DFF", 3) == 0 ) // works for both DFF and DFFRSE
            {
                if ( Vec_PtrSize(vTokens) == 6 )
                {
                    // create primary input to represent flop output
                    char pNetName[1000]; char * pName; int i;
                    char * pFlopOut   = (char *)vTokens->pArray[0];
                    Abc_Obj_t * pNet  = Abc_NtkFindOrCreateNet( pNtk, pFlopOut );
                    Abc_Obj_t * pTerm = Abc_NtkCreatePi( pNtk );
                    Abc_ObjAddFanin( pNet, pTerm );
                    // create four primary outputs to represent flop inputs
                    Vec_PtrForEachEntryStart( char *, vTokens, pName, i, 2 )
                    {
                        sprintf( pNetName, "%s_%s", pFlopOut, pName );
                        pNet  = Abc_NtkFindOrCreateNet( pNtk, pName );
                        pTerm = Abc_NtkCreateNodeBuf( pNtk, pNet );
                        pNet  = Abc_NtkFindOrCreateNet( pNtk, pNetName );
                        Abc_ObjAddFanin( pNet, pTerm );
                        pTerm = Abc_NtkCreatePo( pNtk );
                        Abc_ObjAddFanin( pTerm, pNet );
                    }
                    pNtk->nConstrs++;
                }
                else
                {
                    pNode = Io_ReadCreateLatch( pNtk, (char *)vTokens->pArray[2], (char *)vTokens->pArray[0] );
    //                Abc_LatchSetInit0( pNode );
                    if ( pType[3] == '0' )
                        Abc_LatchSetInit0( pNode );
                    else if ( pType[3] == '1' )
                        Abc_LatchSetInit1( pNode );
                    else
                        Abc_LatchSetInitDc( pNode );
                }
            }
            else if ( strcmp(pType, "LUT") == 0 )
            {
                fLutsPresent = 1;
                ppNames = (char **)vTokens->pArray + 3;
                nNames  = vTokens->nSize - 3;
                // check the number of inputs
                if ( nNames > 15 )
                {
                    printf( "%s: Currently cannot read truth tables with more than 8 inputs (%d).\n", Extra_FileReaderGetFileName(p), nNames );
                    Vec_StrFree( vString );
                    Abc_NtkDelete( pNtk );
                    return NULL;
                }
                // get the hex string
                pString = (char *)vTokens->pArray[2];
                if ( strncmp( pString, "0x", 2 ) )
                {
                    printf( "%s: The LUT signature (%s) does not look like a hexadecimal beginning with \"0x\".\n", Extra_FileReaderGetFileName(p), pString );
                    Vec_StrFree( vString );
                    Abc_NtkDelete( pNtk );
                    return NULL;
                }
                pString += 2;
                // pad the string with zero's if needed
                nDigits = (1 << nNames) / 4;
                if ( nDigits == 0 )
                    nDigits = 1;
                if ( strlen(pString) < (unsigned)nDigits )
                {
                    Vec_StrFill( vString, nDigits - strlen(pString), '0' );
                    Vec_StrPrintStr( vString, pString );
                    Vec_StrPush( vString, 0 );
                    pString = Vec_StrArray( vString );
                }
                // read the hex number from the string
                if ( !Extra_ReadHexadecimal( uTruth, pString, nNames ) )
                {
                    printf( "%s: Reading hexadecimal number (%s) has failed.\n", Extra_FileReaderGetFileName(p), pString );
                    Vec_StrFree( vString );
                    Abc_NtkDelete( pNtk );
                    return NULL;
                }
                // check if the node is a constant node
                if ( Extra_TruthIsConst0(uTruth, nNames) )
                {
                    pNode = Io_ReadCreateNode( pNtk, (char *)vTokens->pArray[0], ppNames, 0 );
                    Abc_ObjSetData( pNode, Abc_SopRegister( (Mem_Flex_t *)pNtk->pManFunc, " 0\n" ) );
                }
                else if ( Extra_TruthIsConst1(uTruth, nNames) )
                {
                    pNode = Io_ReadCreateNode( pNtk, (char *)vTokens->pArray[0], ppNames, 0 );
                    Abc_ObjSetData( pNode, Abc_SopRegister( (Mem_Flex_t *)pNtk->pManFunc, " 1\n" ) );
                }
                else
                {
                    // create the node
                    pNode = Io_ReadCreateNode( pNtk, (char *)vTokens->pArray[0], ppNames, nNames );
                    assert( nNames > 0 );
                    if ( nNames > 1 )
                        Abc_ObjSetData( pNode, Abc_SopCreateFromTruth((Mem_Flex_t *)pNtk->pManFunc, nNames, uTruth) );
                    else if ( pString[0] == '2' )
                        Abc_ObjSetData( pNode, Abc_SopCreateBuf((Mem_Flex_t *)pNtk->pManFunc) );
                    else if ( pString[0] == '1' )
                        Abc_ObjSetData( pNode, Abc_SopCreateInv((Mem_Flex_t *)pNtk->pManFunc) );
                    else
                    {
                        printf( "%s: Reading truth table (%s) of single-input node has failed.\n", Extra_FileReaderGetFileName(p), pString );
                        Vec_StrFree( vString );
                        Abc_NtkDelete( pNtk );
                        return NULL;
                    }
                }
            }
            else
            {
                // create a new node and add it to the network
                ppNames = (char **)vTokens->pArray + 2;
                nNames  = vTokens->nSize - 2;
                pNode = Io_ReadCreateNode( pNtk, (char *)vTokens->pArray[0], ppNames, nNames );
                // assign the cover
                if ( strcmp(pType, "AND") == 0 || strcmp(pType, "and") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateAnd((Mem_Flex_t *)pNtk->pManFunc, nNames, NULL) );
                else if ( strcmp(pType, "OR") == 0 || strcmp(pType, "or") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateOr((Mem_Flex_t *)pNtk->pManFunc, nNames, NULL) );
                else if ( strcmp(pType, "NAND") == 0 || strcmp(pType, "nand") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateNand((Mem_Flex_t *)pNtk->pManFunc, nNames) );
                else if ( strcmp(pType, "NOR") == 0 || strcmp(pType, "nor") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateNor((Mem_Flex_t *)pNtk->pManFunc, nNames) );
                else if ( strcmp(pType, "XOR") == 0 || strcmp(pType, "xor") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateXor((Mem_Flex_t *)pNtk->pManFunc, nNames) );
                else if ( strcmp(pType, "NXOR") == 0 || strcmp(pType, "XNOR") == 0 || strcmp(pType, "nxor") == 0 || strcmp(pType, "xnor") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateNxor((Mem_Flex_t *)pNtk->pManFunc, nNames) );
                else if ( strncmp(pType, "BUF", 3) == 0 || strcmp(pType, "buf") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateBuf((Mem_Flex_t *)pNtk->pManFunc) );
                else if ( strcmp(pType, "NOT") == 0 || strcmp(pType, "not") == 0 )
                    Abc_ObjSetData( pNode, Abc_SopCreateInv((Mem_Flex_t *)pNtk->pManFunc) );
                else if ( strncmp(pType, "MUX", 3) == 0 || strcmp(pType, "mux") == 0 )
//                    Abc_ObjSetData( pNode, Abc_SopRegister(pNtk->pManFunc, "1-0 1\n-11 1\n") );
                    Abc_ObjSetData( pNode, Abc_SopRegister((Mem_Flex_t *)pNtk->pManFunc, "0-1 1\n11- 1\n") );
                else if ( strncmp(pType, "gnd", 3) == 0 )
                    Abc_ObjSetData( pNode, Abc_SopRegister( (Mem_Flex_t *)pNtk->pManFunc, " 0\n" ) );
                else if ( strncmp(pType, "vdd", 3) == 0 )
                    Abc_ObjSetData( pNode, Abc_SopRegister( (Mem_Flex_t *)pNtk->pManFunc, " 1\n" ) );
                else
                {
                    printf( "Io_ReadBenchNetwork(): Cannot determine gate type \"%s\" in line %d.\n", pType, Extra_FileReaderGetLineNumber(p, 0) );
                    Vec_StrFree( vString );
                    Abc_NtkDelete( pNtk );
                    return NULL;
                }
            }
        }
    }
    Extra_ProgressBarStop( pProgress );
    Vec_StrFree( vString );

    // check if constant 0 is present
    if ( (pNet = Abc_NtkFindNet( pNtk, "gnd" )) )
    {
        if ( Abc_ObjFaninNum(pNet) == 0 )
            Io_ReadCreateConst( pNtk, "gnd", 0 );
    }
    if ( (pNet = Abc_NtkFindNet( pNtk, "1" )) )
    {
        if ( Abc_ObjFaninNum(pNet) == 0 )
        {
            printf( "Io_ReadBenchNetwork(): Adding constant 0 fanin to non-driven net \"1\".\n" );
            Io_ReadCreateConst( pNtk, "1", 0 );
        }
    }
    // check if constant 1 is present
    if ( (pNet = Abc_NtkFindNet( pNtk, "vdd" )) )
    {
        if ( Abc_ObjFaninNum(pNet) == 0 )
            Io_ReadCreateConst( pNtk, "vdd", 1 );
    }
    if ( (pNet = Abc_NtkFindNet( pNtk, "2" )) )
    {
        if ( Abc_ObjFaninNum(pNet) == 0 )
        {
            printf( "Io_ReadBenchNetwork(): Adding constant 1 fanin to non-driven net \"2\".\n" );
            Io_ReadCreateConst( pNtk, "2", 1 );
        }
    }

    Abc_NtkFinalizeRead( pNtk );

    // if LUTs are present, collapse the truth tables into cubes
    if ( fLutsPresent )
    {
        if ( !Abc_NtkToBdd(pNtk) )
        {
            printf( "Io_ReadBenchNetwork(): Converting to BDD has failed.\n" );
            Abc_NtkDelete( pNtk );
            return NULL;
        }
        if ( !Abc_NtkToSop(pNtk, -1, ABC_INFINITY) )
        {
            printf( "Io_ReadBenchNetwork(): Converting to SOP has failed.\n" );
            Abc_NtkDelete( pNtk );
            return NULL;
        }
    }
    return pNtk;
}

int Io_WriteBenchOneNode( FILE * pFile, Abc_Obj_t * pNode )
{
    int nFanins;

    assert( Abc_ObjIsNode(pNode) );
    nFanins = Abc_ObjFaninNum(pNode);
    if ( nFanins == 0 )
    {   // write the constant 1 node
        assert( Abc_NodeIsConst1(pNode) );
        fprintf( pFile, "%-11s",          Abc_ObjName(Abc_ObjFanout0(pNode)) );
        fprintf( pFile, " = vdd\n" );
    }
    else if ( nFanins == 1 )
    {   // write the interver/buffer
        if ( Abc_NodeIsBuf(pNode) )
        {
            fprintf( pFile, "%-11s = BUFF(",  Abc_ObjName(Abc_ObjFanout0(pNode)) );
            fprintf( pFile, "%s)\n",          Abc_ObjName(Abc_ObjFanin0(pNode)) );
        }
        else
        {
            fprintf( pFile, "%-11s = NOT(",   Abc_ObjName(Abc_ObjFanout0(pNode)) );
            fprintf( pFile, "%s)\n",          Abc_ObjName(Abc_ObjFanin0(pNode)) );
        }
    }
    else
    {   // write the AND gate
        fprintf( pFile, "%-11s",       Abc_ObjName(Abc_ObjFanout0(pNode)) );
        fprintf( pFile, " = AND(%s, ", Abc_ObjName(Abc_ObjFanin0(pNode)) );
        fprintf( pFile, "%s)\n",       Abc_ObjName(Abc_ObjFanin1(pNode)) );
    }
    return 1;
}

int Io_WriteBenchOne( FILE * pFile, Abc_Ntk_t * pNtk )
{
    ProgressBar * pProgress;
    Abc_Obj_t * pNode;
    int i;

    // write the PIs/POs/latches
    Abc_NtkForEachPi( pNtk, pNode, i )
        fprintf( pFile, "INPUT(%s)\n", Abc_ObjName(Abc_ObjFanout0(pNode)) );
    Abc_NtkForEachPo( pNtk, pNode, i )
        fprintf( pFile, "OUTPUT(%s)\n", Abc_ObjName(Abc_ObjFanin0(pNode)) );
    Abc_NtkForEachLatch( pNtk, pNode, i )
        fprintf( pFile, "%-11s = DFF(%s)\n",
            Abc_ObjName(Abc_ObjFanout0(Abc_ObjFanout0(pNode))), Abc_ObjName(Abc_ObjFanin0(Abc_ObjFanin0(pNode))) );

    // write internal nodes
    pProgress = Extra_ProgressBarStart( stdout, Abc_NtkObjNumMax(pNtk) );
    Abc_NtkForEachNode( pNtk, pNode, i )
    {
        Extra_ProgressBarUpdate( pProgress, i, NULL );
        Io_WriteBenchOneNode( pFile, pNode );
    }
    Extra_ProgressBarStop( pProgress );
    return 1;
}

char* runAbcCommands(char *pFileContent, const char *sCommand)
{
    Abc_Frame_t *pAbc = Abc_FrameGetGlobalFrame();

    Extra_FileReader_t *p = Extra_FileReaderAllocFromString(pFileContent, "#", "\n\r", " \t,()=");

    Abc_Ntk_t *pNtk = Io_ReadBenchNetwork(p);
    pNtk = Abc_NtkToLogic(pNtk);

    Abc_FrameReplaceCurrentNetwork(pAbc, pNtk);

    Cmd_CommandExecute(pAbc, sCommand);

    Abc_Ntk_t *pNtkTemp = Abc_NtkToNetlistBench(pAbc->pNtkCur);

    char *buffer;
    size_t size;
    FILE *memFile = open_memstream(&buffer, &size);
    Io_WriteBenchOne(memFile, pNtkTemp);
    fclose(memFile);

    return buffer;
}
